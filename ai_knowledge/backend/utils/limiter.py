"""速率限制配置"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_user_key(request: Request) -> str:
    """根据登录状态生成限流 key"""
    auth_header = request.headers.get("Authorization")
    if auth_header:
        return f"user:{auth_header}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_user_key,
    default_limits=["60/minute"],
    storage_uri="memory://",
)