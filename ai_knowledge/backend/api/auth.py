"""认证相关 API"""
from fastapi import APIRouter, Form, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User
from utils.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user
)
from utils.upload import save_uploaded_file
from utils.limiter import limiter
from utils.response import success, error

router = APIRouter()


@router.post("/api/users/register")
@limiter.limit("3/minute")
def register(request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """用户注册"""
    if db.query(User).filter(User.username == username).first():
        error("用户名已存在", status_code=400)

    hashed_pw = get_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.add(new_user)
    db.commit()
    return success(message="注册成功")


@router.post("/api/users/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """用户登录（返回 access_token + refresh_token）"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        error("用户名或密码错误", status_code=401)

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return success(data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "username": username
    })


@router.post("/api/auth/refresh")
@limiter.limit("10/minute")
def refresh_token(
    request: Request,
    refresh_token: str = Form(...),
    db: Session = Depends(get_db)
):
    """使用 refresh_token 获取新的 access_token"""
    payload = decode_token(refresh_token)
    if not payload:
        error("无效的刷新令牌", status_code=401)

    token_type = payload.get("type")
    if token_type != "refresh":
        error("令牌类型错误", status_code=401)

    user_id_str = payload.get("sub")
    if not user_id_str:
        error("无效的刷新令牌", status_code=401)

    user = db.query(User).filter(User.id == int(user_id_str)).first()
    if not user:
        error("用户不存在", status_code=401)

    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return success(data={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    })


@router.get("/api/users/profile")
@router.get("/api/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    """获取用户资料"""
    return success(data={
        "id": current_user.id,
        "name": current_user.name or current_user.username,
        "username": current_user.username,
        "avatar": current_user.avatar,
        "major": current_user.major,
        "grade": current_user.grade,
        "score": current_user.score,
        "role": current_user.role
    })


@router.put("/api/users/profile")
def update_profile(
    username: str = Form(...),
    name: str = Form(""),
    avatar: str = Form(""),
    major: str = Form(""),
    grade: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    current_user.username = username
    current_user.name = name
    current_user.avatar = avatar
    current_user.major = major
    current_user.grade = grade
    db.commit()
    return success(message="用户资料更新成功")


@router.post("/api/profile")
def save_profile(
    name: str = Form(""),
    major: str = Form(""),
    grade: str = Form(""),
    avatar_file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存用户资料（支持头像上传）"""
    if name:
        current_user.name = name
    if major:
        current_user.major = major
    if grade:
        current_user.grade = grade

    if avatar_file:
        avatar_url = save_uploaded_file(avatar_file, allowed_types=["image/"])
        current_user.avatar = avatar_url

    db.commit()

    return success(data={
        "message": "信息保存成功",
        "avatar": current_user.avatar,
        "name": current_user.name,
        "major": current_user.major,
        "grade": current_user.grade
    })