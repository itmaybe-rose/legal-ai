"""文件上传相关工具函数 - 含安全校验"""
import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = "static/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf", ".doc", ".docx",
}

# 常见文件魔数（文件头前几个字节）
MAGIC_BYTES = {
    b"\xff\xd8\xff": [".jpg", ".jpeg"],
    b"\x89PNG\r\n\x1a\n": [".png"],
    b"GIF87a": [".gif"],
    b"GIF89a": [".gif"],
    b"RIFF": [".webp"],
    b"%PDF": [".pdf"],
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": [".doc"],
    b"PK\x03\x04": [".docx"],
}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _check_magic_bytes(file_path: str, expected_ext: str) -> bool:
    """校验文件魔数是否匹配扩展名"""
    with open(file_path, "rb") as f:
        header = f.read(16)
    for magic, exts in MAGIC_BYTES.items():
        if header.startswith(magic):
            return expected_ext in exts
    return False


def save_uploaded_file(file: UploadFile, allowed_types: list = None) -> str:
    """
    安全保存上传的文件
    - 校验扩展名
    - 校验文件大小
    - 校验文件魔数
    - 防止路径穿越
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    if allowed_types and not any(file.content_type.startswith(t) for t in allowed_types):
        raise HTTPException(status_code=400, detail="文件类型不允许")

    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件过大，最大支持 {MAX_FILE_SIZE // (1024*1024)}MB")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if not _check_magic_bytes(file_path, ext):
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="文件内容与扩展名不匹配，疑似伪造文件")

    return f"/static/uploads/{unique_filename}"