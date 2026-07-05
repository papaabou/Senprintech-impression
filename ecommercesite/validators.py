import os

from django.core.exceptions import ValidationError

MAX_UPLOAD_SIZE_MB = 20
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".ai",
    ".eps",
    ".psd",
    ".svg",
    ".doc",
    ".docx",
    ".txt",
}


def validate_upload_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise ValidationError(
            f"Format de fichier non autorise ({ext or 'inconnu'}). Formats acceptes : {allowed}."
        )
    if value.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(
            f"Le fichier est trop volumineux ({value.size / (1024 * 1024):.1f} Mo). Taille maximale : {MAX_UPLOAD_SIZE_MB} Mo."
        )
