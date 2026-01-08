import json
import os
from pathlib import Path
import zipstream
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import FileResponse, Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods
from apps.exams.forms import ContentItemUploadForm
from apps.exams.models import ContentItem, UploadBatch, UploadFile
MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_FILES_PER_BATCH = 10
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".jpg", ".jpeg", ".png", ".txt"}
def upload(request):
    if request.method == "POST":
        form = ContentItemUploadForm(request.POST, request.FILES)
        if form.is_valid():
            content_item = form.save(commit=False)
            content_item.status = ContentItem.Status.PENDING
            content_item.download_count = 0
            content_item.save()
            return redirect("exams:upload_thanks")
    else:
        form = ContentItemUploadForm()
    return render(request, "exams/upload.html", {"form": form})
def upload_thanks(request):
    return render(request, "exams/upload_thanks.html")
def download(request, pk):
    content_item = get_object_or_404(
        ContentItem,
        pk=pk,
        status=ContentItem.Status.APPROVED,
    )
    if not content_item.file:
        raise Http404("File not found.")
    storage = content_item.file.storage
    if not storage.exists(content_item.file.name):
        raise Http404("File not found.")
    ContentItem.objects.filter(pk=pk).update(download_count=F("download_count") + 1)
    try:
        file_handle = content_item.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("File not found.")
    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=os.path.basename(content_item.file.name),
    )
@login_required
def upload_batch_portal(request):
    return render(request, "exams/upload_batch.html")
def _sanitize_zip_name(filename, used_names):
    safe_name = get_valid_filename(Path(filename).name) or "file"
    base = safe_name
    counter = 1
    while safe_name in used_names:
        safe_name = f"{Path(base).stem}-{counter}{Path(base).suffix}"
        counter += 1
    used_names.add(safe_name)
    return safe_name
@require_http_methods(["POST"])
@login_required
def create_upload_batch(request):
    payload = {}
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
    batch = UploadBatch.objects.create(owner=request.user, context=payload.get("context", ""))
    return JsonResponse({"batch_id": batch.id}, status=201)
@require_http_methods(["POST"])
@login_required
def upload_batch_files(request, batch_id):
    batch = get_object_or_404(UploadBatch, pk=batch_id, owner=request.user)
    incoming_files = request.FILES.getlist("files")
    if not incoming_files:
        return JsonResponse({"error": "No files provided."}, status=400)
    existing_count = batch.files.count()
    if existing_count + len(incoming_files) > MAX_FILES_PER_BATCH:
        return JsonResponse({"error": "Too many files in this batch."}, status=400)
    errors = []
    for incoming in incoming_files:
        extension = Path(incoming.name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            errors.append(f"{incoming.name}: unsupported file type.")
        if incoming.size > MAX_FILE_SIZE:
            errors.append(f"{incoming.name}: file too large.")
    if errors:
        return JsonResponse({"errors": errors}, status=400)
    saved_files = []
    for incoming in incoming_files:
        upload_file = UploadFile.objects.create(
            batch=batch,
            file=incoming,
            original_name=incoming.name,
            size=incoming.size,
            mime=incoming.content_type or "",
        )
        saved_files.append({"id": upload_file.id, "name": upload_file.original_name, "size": upload_file.size})
    return JsonResponse({"files": saved_files}, status=201)
@require_http_methods(["DELETE"])
@login_required
def delete_upload_file(request, file_id):
    upload_file = get_object_or_404(UploadFile, pk=file_id, batch__owner=request.user)
    upload_file.file.delete(save=False)
    upload_file.delete()
    return JsonResponse({"deleted": True})
@require_http_methods(["GET"])
@login_required
def download_upload_batch(request, batch_id):
    batch = get_object_or_404(UploadBatch, pk=batch_id, owner=request.user)
    zip_file = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)
    used_names = set()
    for upload_file in batch.files.all().iterator():
        sanitized = _sanitize_zip_name(upload_file.original_name, used_names)
        def file_iter(file_field=upload_file.file):
            with file_field.open("rb") as handle:
                while True:
                    chunk = handle.read(8192)
                    if not chunk:
                        break
                    yield chunk
        zip_file.write_iter(sanitized, file_iter())
    response = StreamingHttpResponse(zip_file, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="batch-{batch_id}.zip"'
    return response
