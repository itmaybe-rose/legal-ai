"""统一响应格式"""
from fastapi import HTTPException
from typing import Any, Optional


def success(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {"code": 0, "message": message, "data": data}


def error(message: str = "error", code: int = 1, status_code: int = 400):
    """错误响应（抛出 HTTPException）"""
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message}
    )