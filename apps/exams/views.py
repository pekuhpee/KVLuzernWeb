import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from django.db.models import F
from django.http import FileResponse, Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods
from apps.exams.forms import UploadBatchForm
from apps.exams.models import ContentItem, MetaCategory, UploadBatch, UploadFile
MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_FILES_PER_BATCH = 10
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".jpg", ".jpeg", ".png", ".zip"}
logger = logging.getLogger(__name__)
def _validate_upload_files(incoming_files, existing_count=0):
    errors = []
    if existing_count + len(incoming_files) > MAX_FILES_PER_BATCH:
        errors.append("Too many files in this batch.")
        return errors
    for incoming in incoming_files:
        extension = Path(incoming.name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            errors.append(f"{incoming.name}: unsupported file type.")
        if incoming.size > MAX_FILE_SIZE:
            errors.append(f"{incoming.name}: file too large.")
    return errors


def upload(request):
    server_errors = []
    form = UploadBatchForm(request.POST or None)
    if request.method == "POST":
        if not request.FILES:
            server_errors = ["Bitte mindestens eine Datei auswählen."]
        elif form.is_valid():
            batch = form.save(commit=False)
            if request.user.is_authenticated:
                batch.owner = request.user
            batch.save()
            _store_batch_token(request, batch)
            incoming_files = request.FILES.getlist("files")
            server_errors = _validate_upload_files(incoming_files)
            if not server_errors:
                for incoming in incoming_files:
                    UploadFile.objects.create(
                        batch=batch,
                        content_type=batch.content_type,
                        category=batch.category,
                        subcategory=batch.subcategory,
                        file=incoming,
                        original_name=incoming.name,
                        size=incoming.size,
                        mime=incoming.content_type or "",
                    )
                return redirect("exams:upload_thanks")
        elif not server_errors:
            server_errors = [
                f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()
            ]
    meta_labels = {
        category.key: category.label
        for category in MetaCategory.objects.filter(is_active=True).order_by("sort_order", "label")
    }
    return render(
        request,
        "exams/upload_batch.html",
        {
            "form": form,
            "meta_labels": meta_labels,
            "max_files": MAX_FILES_PER_BATCH,
            "max_file_size_mb": int(MAX_FILE_SIZE / (1024 * 1024)),
            "allowed_extensions": ", ".join(sorted(ALLOWED_EXTENSIONS)),
            "server_errors": server_errors,
        },
    )
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
    return FileResponse(file_handle, as_attachment=True, filename=os.path.basename(content_item.file.name))
def download_upload_file(request, file_id):
    upload_file = get_object_or_404(
        UploadFile,
        pk=file_id,
        batch__status=UploadBatch.Status.APPROVED,
    )
    if not upload_file.file:
        raise Http404("File not found.")
    storage = upload_file.file.storage
    if not storage.exists(upload_file.file.name):
        raise Http404("File not found.")
    try:
        file_handle = upload_file.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("File not found.")
    return FileResponse(file_handle, as_attachment=True, filename=os.path.basename(upload_file.file.name))
def upload_batch_portal(request):
    return redirect("exams:upload")
def _sanitize_zip_name(filename, used_names):
    safe_name = get_valid_filename(Path(filename).name) or "file"
    base = safe_name
    counter = 1
    while safe_name in used_names:
        safe_name = f"{Path(base).stem}-{counter}{Path(base).suffix}"
        counter += 1
    used_names.add(safe_name)
    return safe_name
def _store_batch_token(request, batch):
    tokens = request.session.get("upload_batch_tokens", {})
    tokens[str(batch.id)] = str(batch.token)
    request.session["upload_batch_tokens"] = tokens
def _get_request_token(request):
    return request.headers.get("X-Upload-Token") or request.POST.get("upload_token") or request.GET.get("upload_token")
def _has_batch_access(request, batch):
    if batch.status == UploadBatch.Status.APPROVED:
        return True
    token = _get_request_token(request)
    session_token = request.session.get("upload_batch_tokens", {}).get(str(batch.id))
    return token and session_token and token == session_token and token == str(batch.token)
@require_http_methods(["POST"])
def create_upload_batch(request):
    payload = {}
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = request.POST
    form = UploadBatchForm(payload)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    try:
        batch = form.save(commit=False)
        batch.context = payload.get("context", "")
        if request.user.is_authenticated:
            batch.owner = request.user
        batch.save()
    except Exception:
        logger.exception("Failed to create upload batch.")
        return JsonResponse(
            {"detail": "Upload-Batch konnte nicht erstellt werden. Bitte Eingaben prüfen."},
            status=500,
        )
    _store_batch_token(request, batch)
    return JsonResponse({"batch_id": batch.id, "upload_token": str(batch.token)}, status=201)
@require_http_methods(["POST"])
def upload_batch_files(request, batch_id):
    batch = get_object_or_404(UploadBatch, pk=batch_id)
    if not _has_batch_access(request, batch):
        return JsonResponse({"error": "Unauthorized."}, status=403)
    incoming_files = request.FILES.getlist("files")
    if not incoming_files:
        return JsonResponse({"error": "No files provided."}, status=400)
    existing_count = batch.files.count()
    errors = _validate_upload_files(incoming_files, existing_count=existing_count)
    if errors:
        return JsonResponse({"errors": errors}, status=400)
    saved_files = []
    for incoming in incoming_files:
        upload_file = UploadFile.objects.create(
            batch=batch,
            content_type=batch.content_type,
            category=batch.category,
            subcategory=batch.subcategory,
            file=incoming,
            original_name=incoming.name,
            size=incoming.size,
            mime=incoming.content_type or "",
        )
        saved_files.append({"id": upload_file.id, "name": upload_file.original_name, "size": upload_file.size})
    return JsonResponse({"files": saved_files}, status=201)
@require_http_methods(["DELETE"])
def delete_upload_file(request, file_id):
    upload_file = get_object_or_404(UploadFile, pk=file_id)
    if not _has_batch_access(request, upload_file.batch):
        return JsonResponse({"error": "Unauthorized."}, status=403)
    upload_file.file.delete(save=False)
    upload_file.delete()
    return JsonResponse({"deleted": True})
@require_http_methods(["GET"])
def download_upload_batch(request, batch_id):
    batch = get_object_or_404(UploadBatch, pk=batch_id)
    if not _has_batch_access(request, batch):
        return JsonResponse({"error": "Unauthorized."}, status=403)
    used_names = set()
    temp_file = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024, mode="w+b")
    with zipfile.ZipFile(temp_file, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, upload_file in enumerate(batch.files.all().order_by("created_at", "id").iterator(), start=1):
            sanitized = _sanitize_zip_name(upload_file.original_name, used_names)
            name = f"{index:02d}_{sanitized}"
            with archive.open(name, "w") as dest, upload_file.file.open("rb") as src:
                shutil.copyfileobj(src, dest, length=8192)
    temp_file.seek(0)
    def stream():
        while True:
            chunk = temp_file.read(8192)
            if not chunk:
                break
            yield chunk
        temp_file.close()

    response = StreamingHttpResponse(stream(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="batch-{batch_id}.zip"'
    return response


@require_http_methods(["GET"])
def download_filtered_zip(request):
    approved_items = ContentItem.objects.filter(status=ContentItem.Status.APPROVED).exclude(file="")
    type_key = request.GET.get("type"); year_key = request.GET.get("year"); subject_key = request.GET.get("subject")
    teacher_key = request.GET.get("teacher"); program_key = request.GET.get("program"); sort = request.GET.get("sort", "newest")
    items = approved_items
    if type_key:
        items = items.filter(content_type=type_key)
    if year_key:
        try:
            items = items.filter(year=int(year_key))
        except ValueError:
            items = items.none()
    if subject_key:
        items = items.filter(subject=subject_key)
    if teacher_key:
        items = items.filter(teacher=teacher_key)
    if program_key:
        items = items.filter(program=program_key)

    if sort == "most_downloaded":
        items = items.order_by("-download_count", "-created_at")
    else:
        items = items.order_by("-created_at")
    used_names = set()
    temp_file = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024, mode="w+b")
    with zipfile.ZipFile(temp_file, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, content_item in enumerate(items.iterator(), start=1):
            if not content_item.file:
                continue
            original_name = os.path.basename(content_item.file.name) or f"item-{content_item.pk}.dat"
            sanitized = _sanitize_zip_name(original_name, used_names)
            name = f"{index:03d}_{sanitized}"
            try:
                with archive.open(name, "w") as dest, content_item.file.open("rb") as src:
                    shutil.copyfileobj(src, dest, length=8192)
            except (FileNotFoundError, OSError):
                continue
    temp_file.seek(0)

    def stream():
        while True:
            chunk = temp_file.read(8192)
            if not chunk:
                break
            yield chunk
        temp_file.close()

    response = StreamingHttpResponse(stream(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="pruefungen.zip"'
    return response
