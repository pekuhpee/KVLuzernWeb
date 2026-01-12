import mimetypes
import os

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404
from django.utils._os import safe_join


def serve_media(request, path):
    if settings.USE_S3_MEDIA:
        raise Http404("Media served via S3.")
    try:
        full_path = safe_join(str(settings.MEDIA_ROOT), path)
    except SuspiciousFileOperation:
        raise Http404("Invalid media path.")
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise Http404("File not found.")
    content_type, _ = mimetypes.guess_type(full_path)
    return FileResponse(open(full_path, "rb"), content_type=content_type)
