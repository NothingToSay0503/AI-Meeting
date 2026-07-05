from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

MP3_CONTENT_TYPES = {"audio/mpeg", "audio/mp3", "audio/x-mpeg"}


def ensure_mp3_file(file: UploadFile) -> None:
    filename = file.filename or ""
    if not filename.lower().endswith(".mp3") or file.content_type not in MP3_CONTENT_TYPES:
        raise ValueError("Only MP3 audio is supported in the first release")


def save_audio_file(file: UploadFile) -> tuple[str, int]:
    ensure_mp3_file(file)

    storage_dir = Path(settings.storage_audio_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    target = storage_dir / f"{uuid4().hex}.mp3"

    file.file.seek(0)
    content = file.file.read()
    target.write_bytes(content)
    return str(target), len(content)
