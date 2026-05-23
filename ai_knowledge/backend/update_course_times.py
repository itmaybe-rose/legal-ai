"""更新课程时间脚本 - 将前端显示的时间同步到数据库"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from models import Course

# 前端显示的时间映射（按节次）
PERIOD_TIME_MAP = {
    '1': {'start': '08:30', 'end': '09:15'},
    '1节': {'start': '08:30', 'end': '09:15'},
    '2': {'start': '09:30', 'end': '10:15'},
    '2节': {'start': '09:30', 'end': '10:15'},
    '1-2': {'start': '08:30', 'end': '10:00'},
    '1-2节': {'start': '08:30', 'end': '10:00'},
    '3': {'start': '10:20', 'end': '11:05'},
    '3节': {'start': '10:20', 'end': '11:05'},
    '4': {'start': '11:15', 'end': '12:00'},
    '4节': {'start': '11:15', 'end': '12:00'},
    '3-4': {'start': '10:20', 'end': '11:50'},
    '3-4节': {'start': '10:20', 'end': '11:50'},
    '5': {'start': '14:00', 'end': '14:45'},
    '5节': {'start': '14:00', 'end': '14:45'},
    '6': {'start': '14:55', 'end': '15:40'},
    '6节': {'start': '14:55', 'end': '15:40'},
    '5-6': {'start': '14:00', 'end': '15:30'},
    '5-6节': {'start': '14:00', 'end': '15:30'},
    '7': {'start': '16:00', 'end': '16:45'},
    '7节': {'start': '16:00', 'end': '16:45'},
    '8': {'start': '16:55', 'end': '17:40'},
    '8节': {'start': '16:55', 'end': '17:40'},
    '7-8': {'start': '16:00', 'end': '17:30'},
    '7-8节': {'start': '16:00', 'end': '17:30'},
    '9': {'start': '18:40', 'end': '19:25'},
    '9节': {'start': '18:40', 'end': '19:25'},
    '10': {'start': '19:35', 'end': '20:20'},
    '10节': {'start': '19:35', 'end': '20:20'},
    '9-10': {'start': '18:40', 'end': '20:10'},
    '9-10节': {'start': '18:40', 'end': '20:10'},
    '11': {'start': '20:30', 'end': '21:15'},
    '11节': {'start': '20:30', 'end': '21:15'},
    '9-11': {'start': '18:40', 'end': '21:30'},
    '9-11节': {'start': '18:40', 'end': '21:30'},
}


def update_course_times():
    """更新所有课程的时间为前端显示的时间"""
    db = next(get_db())

    courses = db.query(Course).all()
    updated_count = 0
    skipped_count = 0

    print(f"开始更新课程时间，共 {len(courses)} 门课程")
    print("-" * 60)

    for course in courses:
        period = course.period

        if period in PERIOD_TIME_MAP:
            time_info = PERIOD_TIME_MAP[period]
            old_start = course.time_start
            old_end = course.time_end

            course.time_start = time_info['start']
            course.time_end = time_info['end']

            print(f"更新课程: {course.name}")
            print(f"  节次: {period}")
            print(f"  时间: {old_start or '(空)'} → {time_info['start']}")
            print(f"  结束: {old_end or '(空)'} → {time_info['end']}")
            print()

            updated_count += 1
        else:
            print(f"跳过课程: {course.name}")
            print(f"  节次: {period} (未找到映射)")
            print()
            skipped_count += 1

    db.commit()

    print("-" * 60)
    print(f"更新完成！")
    print(f"已更新: {updated_count} 门课程")
    print(f"跳过: {skipped_count} 门课程")


if __name__ == "__main__":
    update_course_times()