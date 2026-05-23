"""管理后台相关 API"""
from fastapi import APIRouter, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User, Post, Comment, Like, Major
from utils.security import get_current_user
from utils.response import success, error
from datetime import datetime, timedelta

router = APIRouter()


def check_admin(current_user: User):
    if current_user.role != 1:
        error("需要管理员权限", status_code=403)


@router.get("/api/admin/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统概览统计数据"""
    check_admin(current_user)

    total_users = db.query(User).count()
    total_posts = db.query(Post).count()
    total_comments = db.query(Comment).count()
    total_likes = db.query(Like).count()

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_users = db.query(User).filter(User.create_time >= today).count()
    today_posts = db.query(Post).filter(Post.create_time >= today).count()
    today_comments = db.query(Comment).filter(Comment.create_time >= today).count()

    active_users = db.query(User).order_by(User.score.desc()).limit(10).all()
    user_ids = [u.id for u in active_users]

    post_counts = dict(
        db.query(Post.user_id, func.count(Post.id))
        .filter(Post.user_id.in_(user_ids))
        .group_by(Post.user_id).all()
    )
    comment_counts = dict(
        db.query(Comment.user_id, func.count(Comment.id))
        .filter(Comment.user_id.in_(user_ids))
        .group_by(Comment.user_id).all()
    )

    return success(data={
        "total_users": total_users,
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_likes": total_likes,
        "today_users": today_users,
        "today_posts": today_posts,
        "today_comments": today_comments,
        "active_users": [
            {
                "id": u.id,
                "username": u.username,
                "name": u.name or u.username,
                "score": u.score or 0,
                "post_count": post_counts.get(u.id, 0),
                "comment_count": comment_counts.get(u.id, 0)
            }
            for u in active_users
        ]
    })


@router.get("/api/admin/users")
def get_all_users(
    page: int = 1,
    limit: int = 20,
    keyword: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（管理员专用）"""
    check_admin(current_user)

    query = db.query(User)
    if keyword:
        query = query.filter(
            User.username.contains(keyword) |
            User.name.contains(keyword) |
            User.major.contains(keyword)
        )

    total = query.count()
    users = query.order_by(User.id.desc()).offset((page - 1) * limit).limit(limit).all()

    user_ids = [u.id for u in users]
    post_counts = dict(
        db.query(Post.user_id, func.count(Post.id))
        .filter(Post.user_id.in_(user_ids))
        .group_by(Post.user_id).all()
    )
    comment_counts = dict(
        db.query(Comment.user_id, func.count(Comment.id))
        .filter(Comment.user_id.in_(user_ids))
        .group_by(Comment.user_id).all()
    )

    return success(data={
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "name": u.name or "",
                "major": u.major or "",
                "grade": u.grade or "",
                "role": u.role,
                "score": u.score or 0,
                "create_time": u.create_time,
                "post_count": post_counts.get(u.id, 0),
                "comment_count": comment_counts.get(u.id, 0)
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "limit": limit
    })


@router.put("/api/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户角色（管理员专用）"""
    check_admin(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        error("用户不存在", status_code=404)

    user.role = role
    db.commit()

    return success(message=f"用户角色已更新为 {'管理员' if role == 1 else '学生'}")


@router.delete("/api/admin/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户（管理员专用）"""
    check_admin(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        error("用户不存在", status_code=404)
    if user.id == current_user.id:
        error("不能删除自己", status_code=400)

    db.query(Post).filter(Post.user_id == user_id).delete()
    db.query(Comment).filter(Comment.user_id == user_id).delete()
    db.query(Like).filter(Like.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    return success(message="用户已删除")


@router.get("/api/admin/posts")
def get_all_posts(
    page: int = 1,
    limit: int = 20,
    keyword: str = "",
    status: int = -1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有帖子列表（管理员专用）"""
    check_admin(current_user)

    query = db.query(Post)
    if keyword:
        query = query.filter(
            Post.title.contains(keyword) |
            Post.content.contains(keyword)
        )
    if status >= 0:
        query = query.filter(Post.status == status)

    total = query.count()
    posts = query.order_by(Post.create_time.desc()).offset((page - 1) * limit).limit(limit).all()

    post_ids = [p.id for p in posts]
    comment_counts = dict(
        db.query(Comment.post_id, func.count(Comment.id))
        .filter(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id).all()
    )

    return success(data={
        "posts": [
            {
                "id": p.id,
                "title": p.title,
                "content": p.content[:200] if p.content else "",
                "author": p.user.name or p.user.username if p.user else "匿名用户",
                "author_id": p.user_id,
                "category": p.category,
                "view_count": p.view_count or 0,
                "like_count": p.like_count or 0,
                "comment_count": comment_counts.get(p.id, 0),
                "create_time": p.create_time,
                "status": p.status
            }
            for p in posts
        ],
        "total": total,
        "page": page,
        "limit": limit
    })


@router.put("/api/admin/posts/{post_id}/status")
def update_post_status(
    post_id: int,
    status: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新帖子状态（管理员专用）"""
    check_admin(current_user)

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        error("帖子不存在", status_code=404)

    post.status = status
    db.commit()

    return success(message=f"帖子状态已更新为 {status}")


@router.delete("/api/admin/posts/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除帖子（管理员专用）"""
    check_admin(current_user)

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        error("帖子不存在", status_code=404)

    db.query(Comment).filter(Comment.post_id == post_id).delete()
    db.query(Like).filter(Like.post_id == post_id).delete()
    db.delete(post)
    db.commit()

    return success(message="帖子已删除")


@router.get("/api/admin/comments")
def get_all_comments(
    page: int = 1,
    limit: int = 20,
    keyword: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有评论列表（管理员专用）"""
    check_admin(current_user)

    query = db.query(Comment)
    if keyword:
        query = query.filter(Comment.content.contains(keyword))

    total = query.count()
    comments = query.order_by(Comment.create_time.desc()).offset((page - 1) * limit).limit(limit).all()

    return success(data={
        "comments": [
            {
                "id": c.id,
                "post_id": c.post_id,
                "post_title": c.post.title if c.post else "帖子已删除",
                "content": c.content[:200] if c.content else "",
                "author": c.user.name or c.user.username if c.user else "匿名用户",
                "author_id": c.user_id,
                "parent_id": c.parent_id,
                "create_time": c.create_time,
                "status": c.status
            }
            for c in comments
        ],
        "total": total,
        "page": page,
        "limit": limit
    })


@router.delete("/api/admin/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除评论（管理员专用）"""
    check_admin(current_user)

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        error("评论不存在", status_code=404)

    db.query(Comment).filter(Comment.parent_id == comment_id).delete()
    db.delete(comment)
    db.commit()

    return success(message="评论已删除")


@router.get("/api/admin/majors")
def get_majors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取专业列表（管理员专用）"""
    check_admin(current_user)

    majors = db.query(Major).all()
    return success(data={
        "majors": [
            {
                "id": m.id,
                "name": m.name,
                "college": m.college or ""
            }
            for m in majors
        ]
    })


@router.post("/api/admin/majors")
def add_major(
    name: str = Form(...),
    college: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加专业（管理员专用）"""
    check_admin(current_user)

    existing = db.query(Major).filter(Major.name == name).first()
    if existing:
        error("专业已存在", status_code=400)

    major = Major(name=name, college=college)
    db.add(major)
    db.commit()

    return success(message="专业添加成功", data={"id": major.id})


@router.delete("/api/admin/majors/{major_id}")
def delete_major(
    major_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除专业（管理员专用）"""
    check_admin(current_user)

    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        error("专业不存在", status_code=404)

    db.delete(major)
    db.commit()

    return success(message="专业已删除")


@router.get("/api/admin/categories")
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取论坛帖子分类统计（管理员专用）"""
    check_admin(current_user)

    categories = db.query(Post.category, func.count(Post.id).label("count")).group_by(Post.category).all()

    all_categories = ["讨论", "求助", "分享", "通知"]
    result = []
    for cat in all_categories:
        count = 0
        for c in categories:
            if c[0] == cat:
                count = c[1]
                break
        result.append({"name": cat, "count": count})

    return success(data={"categories": result})