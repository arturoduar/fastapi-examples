"""File uploads and form fields (both need the python-multipart package)."""
import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from ..config import Settings
from ..deps import get_settings
from ..schemas import UploadInfo

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/file", response_model=UploadInfo)
async def upload_file(file: UploadFile, settings: Annotated[Settings, Depends(get_settings)]):
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, f"File larger than {settings.max_upload_bytes} bytes")
    return UploadInfo(filename=file.filename, content_type=file.content_type,
                      size=len(data), sha256=hashlib.sha256(data).hexdigest())


@router.post("/form")
def form_fields(name: Annotated[str, Form(min_length=1)], age: Annotated[int, Form(ge=0, le=150)]):
    return {"name": name, "age": age}
