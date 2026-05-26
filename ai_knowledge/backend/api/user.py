"""用户相关API"""
from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Depends
from fastapi.params import Body
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserSettings, Schedule, Course
from utils.security import get_current_user
from utils.upload import save_uploaded_file
from utils.ai_recognition import recognize_schedule_image
from utils.response import success, error
from utils.logger import logger
import json

router = APIRouter()


@router.get("/api/user/info")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return success(data={
        "id": current_user.id,
        "username": current_user.username,
        "avatar": current_user.avatar,
        "major": current_user.major,
        "goal": current_user.goal
    })


@router.get("/api/options")
def get_options(db: Session = Depends(get_db)):
    """获取专业选项列表"""
    from models import Major
    majors = db.query(Major).all()

    if not majors:
        return success(data={
            "majors": [
                {"name": "计算机科学与技术"},
                {"name": "软件工程"},
                {"name": "人工智能"},
                {"name": "数据科学"},
                {"name": "电子信息"},
                {"name": "自动化"},
                {"name": "机械工程"},
                {"name": "土木工程"},
                {"name": "经济学"},
                {"name": "管理学"},
                {"name": "法学"},
                {"name": "医学"},
                {"name": "教育学"}
            ]
        })

    return success(data={
        "majors": [{"name": m.name} for m in majors]
    })


@router.get("/api/user/settings")
def get_user_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取用户设置"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    if not settings:
        return success(data={
            "home_background": "",
            "home_font_color": "#303133",
            "home_opacity": 0.8,
            "countdown_config": {}
        })

    try:
        if isinstance(settings.countdown_config, str):
            countdown_config = json.loads(settings.countdown_config)
        else:
            countdown_config = settings.countdown_config
    except (json.JSONDecodeError, TypeError):
        countdown_config = {}

    return success(data={
        "home_background": settings.home_background,
        "home_font_color": settings.home_font_color,
        "home_opacity": settings.home_opacity,
        "countdown_config": countdown_config
    })


@router.post("/api/user/settings")
def update_user_settings(
    home_background: str = Form(""),
    home_font_color: str = Form("#303133"),
    home_opacity: float = Form(0.8),
    countdown_config: str = Form("{}"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户设置"""
    try:
        if isinstance(countdown_config, str):
            countdown_config = json.loads(countdown_config)
    except json.JSONDecodeError:
        countdown_config = {}

    if isinstance(countdown_config, dict):
        countdown_config = json.dumps(countdown_config)

    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    if not settings:
        settings = UserSettings(
            user_id=current_user.id,
            home_background=home_background,
            home_font_color=home_font_color,
            home_opacity=home_opacity,
            countdown_config=countdown_config
        )
        db.add(settings)
    else:
        settings.home_background = home_background
        settings.home_font_color = home_font_color
        settings.home_opacity = home_opacity
        settings.countdown_config = countdown_config

    db.commit()
    db.refresh(settings)

    return success(message="用户设置更新成功", data={"settings": settings})


@router.post("/api/user/upload-background")
def upload_background(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传背景图片"""
    url = save_uploaded_file(file, allowed_types=["image/"])
    return success(data={"url": url})


@router.put("/api/user/settings/reminder")
def update_reminder_settings(
    enabled: bool = Body(...),
    minutes: int = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新提醒设置"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    settings.reminder_enabled = enabled
    settings.reminder_minutes = minutes
    db.commit()

    return success(message="提醒设置已更新", data={"enabled": enabled, "minutes": minutes})


@router.get("/api/user/settings/reminder")
def get_reminder_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取提醒设置"""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        return success(data={"enabled": True, "minutes": 20})

    return success(data={
        "enabled": settings.reminder_enabled if settings.reminder_enabled is not None else True,
        "minutes": settings.reminder_minutes if settings.reminder_minutes else 20
    })


@router.get("/api/user/schedule/upcoming")
def get_upcoming_courses(
    minutes: int = 20,
    test_time: str = None,
    test_day: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取即将开始的课程（用于提醒）
    
    Args:
        minutes: 提前多少分钟提醒
        test_time: 测试用，模拟当前时间（格式: HH:MM）
        test_day: 测试用，模拟当前星期（1-7）
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    
    if test_time and test_day:
        try:
            current_date = now.date()
            current_weekday = now.isoweekday()
            days_ahead = (test_day - current_weekday) % 7
            if days_ahead < 0:
                days_ahead += 7
            target_date = current_date + timedelta(days=days_ahead)
            now = datetime.strptime(f"{target_date} {test_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            pass
    elif test_time:
        try:
            now = datetime.strptime(f"{now.date()} {test_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            pass
    
    current_day = test_day if test_day else now.isoweekday()

    schedule = db.query(Schedule).filter(
        Schedule.user_id == current_user.id
    ).order_by(Schedule.created_at.desc()).first()

    if not schedule:
        return success(data={"courses": [], "current_time": now.strftime("%Y-%m-%d %H:%M:%S"), "current_day": current_day})

    courses = db.query(Course).filter(Course.schedule_id == schedule.id).all()
    
    logger.debug(f"Found {len(courses)} courses for schedule {schedule.id}")
    logger.debug(f"Current time: {now}, Current day: {current_day}")

    upcoming = []
    for course in courses:
        if course.day_of_week == current_day:
            logger.debug(f"Found course on day {current_day}: {course.name}, time: {course.time_start}")
            course_time = course.time_start
            if course_time:
                try:
                    course_datetime = datetime.strptime(f"{now.date()} {course_time}", "%Y-%m-%d %H:%M")
                    target_time = course_datetime - timedelta(minutes=minutes)
                    logger.debug(f"Course datetime: {course_datetime}, Target time: {target_time}, Now: {now}")

                    if target_time <= now <= course_datetime:
                        time_diff = (course_datetime - now).total_seconds() / 60
                        if 0 <= time_diff <= minutes:
                            logger.debug(f"Adding course: {course.name}, {time_diff} minutes until start")
                            upcoming.append({
                                "id": course.id,
                                "name": course.name,
                                "day_of_week": course.day_of_week,
                                "period": course.period,
                                "time_start": course.time_start,
                                "time_end": course.time_end,
                                "classroom": course.classroom,
                                "teacher": course.teacher,
                                "color": course.color,
                                "minutes_until_start": int(time_diff)
                            })
                except ValueError as e:
                    logger.error(f"ValueError parsing time {course_time}: {e}")
                    continue
        else:
            logger.debug(f"Course {course.name} is on day {course.day_of_week}, not {current_day}")

    upcoming.sort(key=lambda x: x["minutes_until_start"])
    logger.debug(f"Returning {len(upcoming)} upcoming courses")
    return success(data={"courses": upcoming, "current_time": now.strftime("%Y-%m-%d %H:%M:%S"), "current_day": current_day})


@router.post("/api/user/upload-schedule")
def upload_schedule(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传课程表图片并使用AI识别"""
    url = save_uploaded_file(file, allowed_types=["image/"])

    schedule = Schedule(
        user_id=current_user.id,
        image_url=url
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    import os
    full_image_path = os.path.join("static/uploads", os.path.basename(url))

    result = recognize_schedule_image(full_image_path)

    if result["status"] == "error":
        return error(message=f"课程表识别失败: {result.get('error', '未知错误')}")

    courses_data = result.get("courses", [])
    colors = ["#409eff", "#67c23a", "#f56c6c", "#909399", "#e6a23c", "#f78900", "#7232dd", "#3ba272"]

    for i, course_data in enumerate(courses_data):
        if not course_data.get("name"):
            continue

        course = Course(
            schedule_id=schedule.id,
            name=course_data.get("name", ""),
            day_of_week=course_data.get("day_of_week", 1),
            period=course_data.get("period", ""),
            time_start=course_data.get("time_start", ""),
            time_end=course_data.get("time_end", ""),
            classroom=course_data.get("classroom", ""),
            teacher=course_data.get("teacher", ""),
            color=course_data.get("color", colors[i % len(colors)])
        )
        db.add(course)

    db.commit()

    return success(message="课程表上传成功", data={
        "schedule_id": schedule.id,
        "image_url": url,
        "status": result["status"],
        "courses_count": len(courses_data),
        "auto_accepted": result.get("summary", {}).get("auto_accepted", 0),
        "needs_review": result.get("summary", {}).get("needs_review", 0),
        "needs_fix": result.get("summary", {}).get("needs_fix", 0),
        "violations": result.get("violations", []),
        "low_confidence": [
            {"name": c.get("name", ""), "confidence": c.get("confidence", 0), "warnings": c.get("warnings", [])}
            for c in result.get("low_confidence", [])
        ]
    })


@router.get("/api/user/schedule")
def get_user_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户课程表"""
    schedule = db.query(Schedule).filter(
        Schedule.user_id == current_user.id
    ).order_by(Schedule.created_at.desc()).first()

    if not schedule:
        return success(data={"courses": [], "image_url": ""})

    courses = db.query(Course).filter(Course.schedule_id == schedule.id).all()

    return success(data={
        "image_url": schedule.image_url,
        "courses": [
            {
                "id": c.id,
                "name": c.name,
                "day_of_week": c.day_of_week,
                "period": c.period,
                "time_start": c.time_start,
                "time_end": c.time_end,
                "classroom": c.classroom,
                "teacher": c.teacher,
                "color": c.color
            } for c in courses
        ]
    })


@router.post("/api/user/schedule/course")
def add_course(
    course_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加课程"""
    name = course_data.get("name")
    day_of_week = course_data.get("day_of_week")
    period = course_data.get("period")
    time_start = course_data.get("time_start", "")
    time_end = course_data.get("time_end", "")
    classroom = course_data.get("classroom", "")
    teacher = course_data.get("teacher", "")

    if not name or not day_of_week or not period:
        error("缺少必填参数")

    schedule = db.query(Schedule).filter(
        Schedule.user_id == current_user.id
    ).order_by(Schedule.created_at.desc()).first()

    if not schedule:
        schedule = Schedule(user_id=current_user.id)
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

    colors = ["#409eff", "#67c23a", "#f56c6c", "#909399", "#e6a23c", "#f78900", "#7232dd", "#3ba272"]
    color = colors[hash(name) % len(colors)]

    course = Course(
        schedule_id=schedule.id,
        name=name,
        day_of_week=day_of_week,
        period=period,
        time_start=time_start,
        time_end=time_end,
        classroom=classroom,
        teacher=teacher,
        color=color
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return success(message="课程添加成功", data={"course": {
        "id": course.id,
        "name": course.name,
        "day_of_week": course.day_of_week,
        "period": course.period,
        "time_start": course.time_start,
        "time_end": course.time_end,
        "classroom": course.classroom,
        "teacher": course.teacher,
        "color": course.color
    }})


@router.delete("/api/user/schedule/course/{course_id}")
def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除课程"""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        error("课程不存在", status_code=404)

    schedule = db.query(Schedule).filter(Schedule.id == course.schedule_id).first()
    if schedule.user_id != current_user.id:
        error("无权删除该课程", status_code=403)

    db.delete(course)
    db.commit()

    return success(message="课程删除成功")