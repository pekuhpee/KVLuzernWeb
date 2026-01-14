import re
import zipfile
from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils.text import get_valid_filename

MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_FILES_PER_SUBMISSION = 10
MAX_ZIP_ENTRIES = 200
MAX_ZIP_TOTAL_UNCOMPRESSED = 150 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "xlsx", "png", "jpg", "jpeg", "zip"}
BLOCKED_EXTENSIONS = {
    "bat",
    "cmd",
    "com",
    "dll",
    "exe",
    "jar",
    "js",
    "msi",
    "ps1",
    "py",
    "rb",
    "scr",
    "sh",
    "vbs",
}

ALLOWED_MIME_TYPES = {
    "pdf": {"application/pdf"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "png": {"image/png"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "zip": {"application/zip", "application/x-zip-compressed"},
}

try:
    import magic  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    magic = None


def sanitize_filename(name: str) -> str:
    base_name = Path(name or "").name
    cleaned = base_name.replace("\r", "").replace("\n", "").replace("\x00", "")
    cleaned = cleaned.replace("\"", "").replace("'", "")
    cleaned = cleaned.strip()
    cleaned = get_valid_filename(cleaned) or "file"
    cleaned = cleaned.replace("..", "").strip()
    if cleaned in {"", ".", ".."}:
        return "file"
    return cleaned


def _read_header(uploaded_file, length=8) -> bytes:
    try:
        uploaded_file.seek(0)
        return uploaded_file.read(length)
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass


def _sniff_mime(uploaded_file) -> str:
    header = _read_header(uploaded_file, length=8)
    if magic:
        try:
            return magic.from_buffer(header, mime=True)
        except Exception:
            return ""
    if header.startswith(b"%PDF"):
        return "application/pdf"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header.startswith(b"PK\x03\x04"):
        return "application/zip"
    return ""


def _is_unsafe_zip_path(name: str) -> bool:
    normalized = name.replace("\\", "/")
    if normalized.startswith(("/", "\\")):
        return True
    if re.match(r"^[A-Za-z]:", normalized):
        return True
    parts = [part for part in normalized.split("/") if part and part != "."]
    return ".." in parts


def validate_uploaded_file(uploaded_file) -> None:
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValidationError("Die Datei ist zu gross. Maximal 15 MB erlaubt.")
    name = uploaded_file.name or ""
    extension = Path(name).suffix.lower().lstrip(".")
    if not extension:
        raise ValidationError("Dateien müssen eine gültige Dateiendung besitzen.")
    if extension in BLOCKED_EXTENSIONS:
        raise ValidationError("Ausführbare oder skriptbasierte Dateien sind nicht erlaubt.")
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError("Dateityp nicht erlaubt.")
    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    allowed_types = ALLOWED_MIME_TYPES.get(extension)
    if content_type and allowed_types and content_type not in allowed_types:
        raise ValidationError("Der Dateityp stimmt nicht mit dem Inhalt überein.")
    detected = _sniff_mime(uploaded_file)
    if not detected:
        raise ValidationError("Der Dateityp konnte nicht verifiziert werden.")
    if extension in {"zip", "docx", "pptx", "xlsx"} and detected != "application/zip":
        raise ValidationError("Die Datei entspricht nicht dem erwarteten ZIP-Format.")
    if extension == "pdf" and detected != "application/pdf":
        raise ValidationError("Die Datei ist kein gültiges PDF.")
    if extension in {"jpg", "jpeg"} and detected != "image/jpeg":
        raise ValidationError("Die Datei ist kein gültiges JPG.")
    if extension == "png" and detected != "image/png":
        raise ValidationError("Die Datei ist kein gültiges PNG.")
    if extension == "zip":
        inspect_zip_upload(uploaded_file)


def inspect_zip_upload(uploaded_file) -> None:
    try:
        uploaded_file.seek(0)
        with zipfile.ZipFile(uploaded_file) as archive:
            members = archive.infolist()
            if len(members) > MAX_ZIP_ENTRIES:
                raise ValidationError("ZIP enthält zu viele Dateien.")
            total_size = 0
            for member in members:
                if member.flag_bits & 0x1:
                    raise ValidationError("Passwortgeschützte ZIPs sind nicht erlaubt.")
                if _is_unsafe_zip_path(member.filename):
                    raise ValidationError("ZIP enthält ungültige Pfade.")
                if member.is_dir():
                    continue
                member_ext = Path(member.filename).suffix.lower().lstrip(".")
                if not member_ext:
                    raise ValidationError("ZIP enthält Dateien ohne Erweiterung.")
                if member_ext in BLOCKED_EXTENSIONS or member_ext not in ALLOWED_EXTENSIONS:
                    raise ValidationError("ZIP enthält unzulässige Dateitypen.")
                total_size += member.file_size
                if total_size > MAX_ZIP_TOTAL_UNCOMPRESSED:
                    raise ValidationError("ZIP überschreitet die maximale entpackte Gesamtgrösse.")
    except zipfile.BadZipFile as exc:
        raise ValidationError("ZIP-Datei ist beschädigt.") from exc
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
