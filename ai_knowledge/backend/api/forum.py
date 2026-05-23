"""论坛相关 API"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Post, Comment, Like, User
from utils.security import get_current_user
from utils.upload import save_uploaded_file
from utils.sanitize import sanitize_html
from utils.response import success, error
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


class PostCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = "讨论"


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


class CommentCreate(BaseModel):
    post_id: int
    content: str
    parent_id: Optional[int] = None


STATUS_LABELS = {0: "正常", 1: "审核中", 2: "违规"}


def format_post(post):
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author": post.user.name or post.user.username if post.user else "匿名用户",
        "username": post.user.name or post.user.username if post.user else "匿名用户",
        "category": post.category,
        "create_time": post.create_time,
        "likes": post.like_count or 0,
        "views": post.view_count or 0,
        "view_count": post.view_count or 0,
        "like_count": post.like_count or 0,
        "status": post.status or 0,
        "status_label": STATUS_LABELS.get(post.status or 0, "未知")
    }


@router.get("/api/forum/posts")
def get_posts(
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取帖子列表（仅显示正常帖子）"""
    user_id = current_user.id if current_user else None
    posts = db.query(Post).filter(Post.status == 0).order_by(Post.create_time.desc()).offset((page - 1) * limit).limit(limit).all()
    return success(data=[format_post(p) for p in posts])


@router.get("/api/forum/posts/{post_id}")
def get_post_detail(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取帖子详情（检查状态权限）"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        error("帖子不存在", status_code=404)

    user_id = current_user.id if current_user else None
    is_author = post.user_id == user_id

    if post.status != 0 and not is_author:
        error("帖子不存在或已被隐藏", status_code=404)

    post.view_count = (post.view_count or 0) + 1
    db.commit()

    result = format_post(post)
    if post.status == 1 and is_author:
        result["status_message"] = "你的帖子正在审核中，审核通过后将对其他用户可见"
    elif post.status == 2 and is_author:
        result["status_message"] = "你的帖子因违反社区规定已被设为违规状态，仅你自己可见"

    return success(data=result)


@router.post("/api/forum/posts")
def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建帖子"""
    new_post = Post(
        title=sanitize_html(post_data.title),
        content=sanitize_html(post_data.content),
        category=post_data.category or "讨论",
        user_id=current_user.id if current_user else None
    )
    db.add(new_post)
    db.commit()
    return success(message="帖子发布成功", data={"post_id": new_post.id})


@router.put("/api/forum/posts/{post_id}")
def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新帖子"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        error("帖子不存在", status_code=404)

    if post.user_id != current_user.id and current_user.role != 1:
        error("无权限修改此帖子", status_code=403)

    if post_data.title:
        post.title = sanitize_html(post_data.title)
    if post_data.content:
        post.content = sanitize_html(post_data.content)
    if post_data.category:
        post.category = post_data.category

    db.commit()
    return success(message="帖子更新成功")


@router.delete("/api/forum/posts/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除帖子"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        error("帖子不存在", status_code=404)

    if post.user_id != current_user.id and current_user.role != 1:
        error("无权限删除此帖子", status_code=403)

    db.query(Comment).filter(Comment.post_id == post_id).delete()
    db.query(Like).filter(Like.post_id == post_id).delete()
    db.delete(post)
    db.commit()
    return success(message="帖子删除成功")


@router.post("/api/forum/comments")
def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建评论"""
    post = db.query(Post).filter(Post.id == comment_data.post_id).first()
    if not post:
        error("帖子不存在", status_code=404)
    if post.status != 0:
        error("无法评论当前状态的帖子", status_code=400)

    new_comment = Comment(
        post_id=comment_data.post_id,
        content=sanitize_html(comment_data.content),
        user_id=current_user.id if current_user else None,
        parent_id=comment_data.parent_id
    )
    db.add(new_comment)
    db.commit()
    return success(message="评论发布成功", data={"comment_id": new_comment.id})


@router.post("/api/forum/posts/{post_id}/like")
def like_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """点赞帖子"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        error("帖子不存在", status_code=404)

    existing_like = db.query(Like).filter(Like.user_id == current_user.id, Like.post_id == post_id).first()
    if not existing_like:
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.add(new_like)
        post.like_count = (post.like_count or 0) + 1
        db.commit()

    return success(message="点赞成功", data={"likes": post.like_count})


@router.get("/api/forum/my-posts")
def get_my_posts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户发布的帖子（含状态信息）"""
    posts = db.query(Post).filter(Post.user_id == current_user.id).order_by(Post.create_time.desc()).all()
    return success(data=[format_post(p) for p in posts])


@router.get("/api/forum/likes")
def get_likes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户点赞的帖子"""
    likes = db.query(Like).filter(Like.user_id == current_user.id).all()
    post_ids = [l.post_id for l in likes]
    posts = db.query(Post).filter(Post.id.in_(post_ids), Post.status == 0).all()
    return success(data=[format_post(p) for p in posts])


@router.get("/api/forum/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    """获取帖子评论"""
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    return success(data=[
        {
            "id": c.id,
            "post_id": c.post_id,
            "content": c.content,
            "author": c.user.name or c.user.username if c.user else "匿名用户",
            "username": c.user.name or c.user.username if c.user else "匿名用户",
            "avatar": c.user.avatar if hasattr(c, 'user') and c.user else None,
            "parent_id": c.parent_id,
            "create_time": c.create_time
        }
        for c in comments
    ])


@router.post("/api/forum/upload")
def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传论坛文件"""
    url = save_uploaded_file(file, allowed_types=["image/", "application/"])
    return success(data={"url": url})


@router.get("/api/my/posts")
def get_my_posts_v2(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取我的帖子（含状态信息）"""
    posts = db.query(Post).filter(Post.user_id == current_user.id).order_by(Post.create_time.desc()).all()
    return success(data=[format_post(p) for p in posts])


@router.get("/api/my/likes")
def get_my_likes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取我的点赞"""
    likes = db.query(Like).filter(Like.user_id == current_user.id).all()
    post_ids = [l.post_id for l in likes]
    posts = db.query(Post).filter(Post.id.in_(post_ids)).all()
    return success(data=[format_post(p) for p in posts])