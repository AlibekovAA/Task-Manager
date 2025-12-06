import mimetypes
import os


def get_content_type(filename: str) -> str:
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


def get_file_size(file_data: bytes) -> int:
    return len(file_data)


def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
    return file_size <= max_size


def validate_file_type(filename: str) -> bool:
    allowed_extensions = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".gif", ".txt"}
    file_extension = os.path.splitext(filename)[1].lower()
    return file_extension in allowed_extensions


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    return "".join(c if c.isalnum() or c in ".-_" else "_" for c in filename)
