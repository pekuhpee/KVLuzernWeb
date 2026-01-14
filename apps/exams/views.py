import json
import logging
import os
import zipfile
from pathlib import Path

from django.db.models import F
from django.http import FileResponse, Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods
import zipstream
from django.core.files.storage import default_storage
from apps.exams.forms import UploadBatchForm
from apps.exams.models import ContentItem, MetaCategory, UploadBatch, UploadFile
MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_FILES_PER_BATCH = 10
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".jpg", ".jpeg", ".png", ".zip"}
ALLOWED_MIME_TYPES = {".pdf": {"application/pdf"}, ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}, ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"}, ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, ".jpg": {"image/jpeg"}, ".jpeg": {"image/jpeg"}, ".png": {"image/png"}, ".zip": {"application/zip", "application/x-zip-compressed"}}
BLOCKED_ZIP_EXTENSIONS = {".exe", ".bat", ".cmd", ".ps1", ".js", ".dll", ".sh"}
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
        content_type = (incoming.content_type or "").lower()
        if extension in ALLOWED_MIME_TYPES and content_type not in ALLOWED_MIME_TYPES[extension]:
            errors.append(f"{incoming.name}: invalid file type.")
        if extension == ".zip":
            try:
                incoming.seek(0)
                with zipfile.ZipFile(incoming) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        member_path = Path(member.filename)
                        if member_path.is_absolute() or ".." in member_path.parts:
                            errors.append(f"{incoming.name}: ZIP enthält ungültige Pfade.")
                            break
                        if member_path.suffix.lower() in BLOCKED_ZIP_EXTENSIONS:
                            errors.append(f"{incoming.name}: ZIP enthält ausführbare Dateien.")
                            break
            except zipfile.BadZipFile:
                errors.append(f"{incoming.name}: ZIP-Datei ist beschädigt.")
            finally:
                incoming.seek(0)
    return errors


def upload(request):
    server_errors = []
    form = UploadBatchForm(request.POST or None)
    if request.method == "POST":
        incoming_files = request.FILES.getlist("files")
        if not incoming_files:
            server_errors = ["Bitte mindestens eine Datei auswählen."]
        elif form.is_valid():
            server_errors = _validate_upload_files(incoming_files)
            if not server_errors:
                batch = form.save(commit=False)
                if request.user.is_authenticated:
                    batch.owner = request.user
                batch.save()
                _store_batch_token(request, batch)
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
                return redirect("exams:upload_success", batch_id=batch.id)
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


def upload_success(request, batch_id):
    batch = get_object_or_404(UploadBatch.objects.select_related("type_option", "year_option", "subject_option", "program_option", "teacher"), pk=batch_id)
    if not _has_batch_access(request, batch):
        raise Http404("Not found.")
    return render(request, "exams/upload_thanks.html", {"batch": batch, "file_count": batch.files.count()})
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
    response = FileResponse(file_handle, as_attachment=True, filename=os.path.basename(content_item.file.name))
    response["X-Content-Type-Options"] = "nosniff"
    return response
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
    response = FileResponse(file_handle, as_attachment=True, filename=os.path.basename(upload_file.file.name))
    response["X-Content-Type-Options"] = "nosniff"
    return response
def upload_batch_portal(request):
    return redirect("exams:upload")
def _sanitize_zip_name(filename):
    base_name = Path(filename or "").name
    safe_name = get_valid_filename(base_name) or "file"
    safe_name = safe_name.replace("..", "").strip()
    if safe_name in {"", ".", ".."}:
        safe_name = "file"
    return safe_name


def _unique_zip_path(prefix, filename, used_paths):
    candidate = f"{prefix}/{filename}"
    if candidate not in used_paths:
        used_paths.add(candidate)
        return candidate
    stem = Path(filename).stem or "file"
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = f"{prefix}/{stem}-{counter}{suffix}"
        if candidate not in used_paths:
            used_paths.add(candidate)
            return candidate
        counter += 1


def _iter_storage_chunks(file_name):
    try:
        file_handle = default_storage.open(file_name, "rb")
    except (FileNotFoundError, OSError, ValueError):
        logger.warning("Failed to open file for ZIP: %s", file_name)
        return None
    if hasattr(file_handle, "chunks"):
        def generator():
            try:
                for chunk in file_handle.chunks():
                    yield chunk
            finally:
                try:
                    file_handle.close()
                except Exception:
                    logger.warning("Failed to close file handle for ZIP: %s", file_name)
        return generator()
    def generator():
        try:
            while True:
                chunk = file_handle.read(8192)
                if not chunk:
                    break
                yield chunk
        finally:
            try:
                file_handle.close()
            except Exception:
                logger.warning("Failed to close file handle for ZIP: %s", file_name)
    return generator()


def build_zip_response(file_items, filename):
    used_paths = set()
    archive = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)
    added_files = 0
    for upload_file in file_items:
        if not upload_file.file or not upload_file.file.name:
            continue
        if not default_storage.exists(upload_file.file.name):
            continue
        sanitized = _sanitize_zip_name(upload_file.original_name)
        prefix = f"submission_{upload_file.batch_id}"
        zip_path = _unique_zip_path(prefix, sanitized, used_paths)
        chunk_iter = _iter_storage_chunks(upload_file.file.name)
        if not chunk_iter:
            continue
        archive.write_iter(zip_path, chunk_iter)
        added_files += 1
    if added_files == 0:
        raise Http404("No files available for download.")
    response = StreamingHttpResponse(archive, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response
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
    batch = get_object_or_404(
        UploadBatch,
        pk=batch_id,
        status=UploadBatch.Status.APPROVED,
    )
    UploadBatch.objects.filter(pk=batch_id).update(download_count=F("download_count") + 1)
    return build_zip_response(
        batch.files.all().order_by("created_at", "id").iterator(),
        f"batch-{batch_id}.zip",
    )


@require_http_methods(["GET"])
def download_filtered_zip(request):
    approved_batches = UploadBatch.objects.filter(status=UploadBatch.Status.APPROVED)
    type_key = request.GET.get("type"); year_key = request.GET.get("year"); subject_key = request.GET.get("subject")
    teacher_key = request.GET.get("teacher"); program_key = request.GET.get("program")
    batches = approved_batches
    if type_key:
        batches = batches.filter(type_option__value_key=type_key)
    if year_key:
        batches = batches.filter(year_option__value_key=year_key)
    if subject_key:
        batches = batches.filter(subject_option__value_key=subject_key)
    if teacher_key:
        batches = batches.filter(teacher__name=teacher_key)
    if program_key:
        batches = batches.filter(program_option__value_key=program_key)

    batches = batches.order_by("-created_at")
    files = UploadFile.objects.filter(batch__in=batches).order_by("batch__created_at", "id")
    return build_zip_response(files.iterator(), "pruefungen.zip")
