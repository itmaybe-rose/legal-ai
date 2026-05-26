"""AI图片识别服务 - 用于识别课程表图片"""
import os
import base64
import json
import re
import requests
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

TIME_PATTERN = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
DAY_PATTERN = re.compile(r'^[1-7]$')
PERIOD_PATTERN = re.compile(r'^\d+([-\d]*)?节?$')

PERIOD_TIME_MAP = {
    "1-2节": ("08:30", "10:00"),
    "3-4节": ("10:20", "11:50"),
    "5-6节": ("14:00", "15:30"),
    "7-8节": ("15:50", "17:20"),
    "9-11节": ("18:40", "20:10"),
}


def validate_time(time_str: str) -> str:
    """校验并标准化时间格式"""
    if not time_str:
        return ""
    time_str = str(time_str).strip()
    if TIME_PATTERN.match(time_str):
        return time_str
    match = re.search(r'(\d{1,2}:\d{2})', time_str)
    if match:
        return match.group(1)
    return ""


def validate_day(day) -> int:
    """校验星期几"""
    try:
        day_int = int(day)
        if 1 <= day_int <= 7:
            return day_int
    except (ValueError, TypeError):
        pass
    return 1


def validate_period(period: str) -> str:
    """校验节次格式"""
    if not period:
        return ""
    period_str = str(period).strip()
    if PERIOD_PATTERN.match(period_str.replace('节', '')):
        period_str = period_str.replace('节', '节')
        if not period_str.endswith('节'):
            period_str += '节'
        return period_str
    match = re.search(r'(\d+[-到至]\d+)', period_str)
    if match:
        return match.group(1) + '节'
    return period_str


def extract_teacher_from_name(name: str) -> Tuple[str, str]:
    """从课程名称中提取教师姓名（处理识别时混在一起的情况）"""
    common_surnames = ['李', '王', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴',
                       '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '罗', '高',
                       '郑', '梁', '谢', '宋', '唐', '许', '邓', '冯', '韩', '曹',
                       '曾', '彭', '萧', '蔡', '潘', '田', '董', '袁', '于', '余']

    if not name:
        return name, ""

    for surname in common_surnames:
        if surname in name:
            idx = name.find(surname)
            if idx > 0 and idx < len(name) - 1:
                candidate = name[idx:]
                if len(candidate) >= 2 and len(candidate) <= 4:
                    return name[:idx].strip(), candidate.strip()
    return name, ""


def is_reasonable_time(time_start: str, time_end: str) -> bool:
    """判断课程时间是否合理（课程时长应在45-120分钟）"""
    try:
        if not time_start or not time_end:
            return True
        t1 = datetime.strptime(time_start, "%H:%M")
        t2 = datetime.strptime(time_end, "%H:%M")
        diff = (t2 - t1).total_seconds() / 60
        return 45 <= diff <= 120
    except (ValueError, TypeError):
        return True


def infer_time_from_period(period: str) -> Optional[Tuple[str, str]]:
    """
    根据节次推断时间
    :param period: 节次，如 "1-2节", "3-4节"
    :return: (time_start, time_end) 或 None
    """
    if not period:
        return None

    period_clean = period.replace('节', '').strip()
    
    for key, (start, end) in PERIOD_TIME_MAP.items():
        key_clean = key.replace('节', '')
        if key_clean == period_clean:
            return (start, end)
    
    return None


def is_reasonable_period_time(period: str, time_start: str) -> bool:
    """判断节次与时间是否匹配"""
    if not period or not time_start:
        return True

    expected_time = infer_time_from_period(period)
    if expected_time:
        expected_start = datetime.strptime(expected_time[0], "%H:%M")
        actual_start = datetime.strptime(time_start, "%H:%M")
        diff_minutes = abs((actual_start - expected_start).total_seconds() / 60)
        return diff_minutes <= 30

    return True


def calculate_confidence(course: dict) -> float:
    """
    根据规则计算识别置信度 (0.0 - 1.0)
    核心逻辑：优先根据节次推断时间，而不是依赖 AI 识别的时间
    """
    score = 1.0
    warnings = []

    name = course.get("name", "")
    time_start = course.get("time_start", "")
    time_end = course.get("time_end", "")
    classroom = course.get("classroom", "")
    period = course.get("period", "")

    # 核心修改：如果有节次，优先根据节次推断时间
    if period:
        inferred_time = infer_time_from_period(period)
        if inferred_time:
            # 使用推断的时间覆盖 AI 识别的时间
            course["time_start"] = inferred_time[0]
            course["time_end"] = inferred_time[1]
            time_start, time_end = inferred_time
        else:
            score -= 0.1
            warnings.append("无法根据节次推断时间")
    else:
        score -= 0.1
        warnings.append("节次信息缺失")

    if not name or len(name) < 2:
        score -= 0.3
        warnings.append("课程名称异常")
    elif len(name) > 30:
        score -= 0.15
        warnings.append("课程名称过长")

    if not time_start or not time_end:
        score -= 0.2
        warnings.append("时间信息不完整")
    elif not is_reasonable_time(time_start, time_end):
        score -= 0.2
        warnings.append("课程时长异常")

    if not classroom:
        score -= 0.1
        warnings.append("教室信息缺失")

    confidence = max(0.0, min(1.0, score))
    course["confidence"] = round(confidence, 2)
    course["warnings"] = warnings

    return confidence


def validate_business_rules(courses: List[dict]) -> Dict:
    """
    业务规则校验，检查冲突课程
    返回: {violations: [], low_confidence: []}
    """
    violations = []
    low_confidence = []
    day_period_map = {}

    for course in courses:
        conf = course.get("confidence", 1.0)
        if conf < 0.7:
            low_confidence.append(course)

        key = (course.get("day_of_week"), course.get("period"))
        if key[0] and key[1]:
            if key in day_period_map:
                violations.append({
                    "course": course.get("name", ""),
                    "day_of_week": key[0],
                    "period": key[1],
                    "reason": "同一时间段存在多门课程",
                    "conflict_with": day_period_map[key]
                })
            else:
                day_period_map[key] = course.get("name", "")

    return {
        "violations": violations,
        "low_confidence": low_confidence
    }


def mark_for_confirmation(courses: List[dict]) -> Dict:
    """
    标记需要用户确认的课程，返回分级结果
    """
    confirmed = []
    uncertain = []
    rejected = []

    for course in courses:
        conf = course.get("confidence", 1.0)

        if conf >= 0.8:
            course["status"] = "confirmed"
            confirmed.append(course)
        elif conf >= 0.6:
            course["status"] = "needs_review"
            uncertain.append(course)
        else:
            course["status"] = "needs_fix"
            rejected.append(course)

    return {
        "confirmed": confirmed,
        "uncertain": uncertain,
        "rejected": rejected,
        "summary": {
            "total": len(courses),
            "auto_accepted": len(confirmed),
            "needs_review": len(uncertain),
            "needs_fix": len(rejected)
        }
    }


def validate_course(course: dict) -> Optional[dict]:
    """校验并标准化单条课程数据"""
    colors = ["#409eff", "#67c23a", "#f56c6c", "#909399", "#e6a23c", "#f78900", "#7232dd", "#3ba272"]

    name = str(course.get("name", "")).strip() if course.get("name") else ""

    if name and not course.get("teacher"):
        name, teacher = extract_teacher_from_name(name)
        if teacher:
            course["teacher"] = teacher

    validated = {
        "name": name,
        "day_of_week": validate_day(course.get("day_of_week")),
        "period": validate_period(course.get("period", "")),
        "time_start": validate_time(course.get("time_start", "")),
        "time_end": validate_time(course.get("time_end", "")),
        "classroom": str(course.get("classroom", "")).strip() if course.get("classroom") else "",
        "teacher": str(course.get("teacher", "")).strip() if course.get("teacher") else "",
    }

    if not validated["name"]:
        return None

    color = course.get("color", "")
    if color and re.match(r'^#[0-9a-fA-F]{6}$', str(color)):
        validated["color"] = color
    else:
        name_hash = sum(ord(c) for c in validated["name"])
        validated["color"] = colors[name_hash % len(colors)]

    calculate_confidence(validated)

    return validated


def recognize_schedule_image(image_path: str) -> Dict:
    """
    使用阿里云通义千问视觉模型(qwen3-vl-plus)识别课程表图片
    采用思维链（CoT）策略，提高识别准确率

    :param image_path: 图片文件路径
    :return: {
        "status": "success" | "needs_review" | "error",
        "courses": [...],
        "summary": {...},
        "violations": [...],
        "low_confidence": [...]
    }
    """
    if not DASHSCOPE_API_KEY:
        logger.warning("未配置DASHSCOPE_API_KEY")
        return {
            "status": "error",
            "error": "未配置DASHSCOPE_API_KEY",
            "courses": [],
            "summary": {}
        }

    try:
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
        }

        prompt = """你是专业的课程表识别助手。请仔细分析图片，严格按照以下思维链步骤执行：

# 思维链（Chain of Thought）
Step 1: 【布局分析】先观察整体结构，确认：
   - 横向/纵向哪个方向表示星期（周一至周日）
   - 横向/纵向哪个方向表示节次（1-2节、3-4节等）
   - 记录表头位置和节次标识位置

Step 2: 【坐标系建立】建立虚拟坐标系：
   - 星期 = X轴（周一=1, 周二=2...周日=7）
   - 节次 = Y轴（1-2节=1, 3-4节=2...）
   - 每个课程对应 (X, Y) 坐标

Step 3: 【逐格识别】从左上角开始，逐格扫描：
   - 识别课程名称（最长且最显眼的文字）
   - 识别教师姓名（通常在课程名后，2-4字）
   - 识别教室（通常包含楼号+房间号，如"4-B105"）
   - 记录该课程的 (X, Y) 坐标

Step 4: 【信息分离】严格分离字段：
   - 课程名称 = 学科名（如"高等数学"）
   - 教师姓名 = 人名（2-4字）
   - 教室 = 地点（如"教学楼A301"）
   - 不要把"(周)"、"第X周"放到教师字段！

Step 5: 【格式标准化】将坐标映射到输出字段：
   - X坐标 → day_of_week
   - Y坐标 → period（根据位置推断节次）
   - 时间信息根据节次推断即可

# 关键规则
✅ 如果课程跨多格（如跨两列），只识别1次，不要重复
✅ 只识别有文字的格子，空的跳过
✅ 教室优先识别带"楼"、"室"、"号"的位置
✅ 姓名优先识别2-4字且不是课程术语的文字

# 输出格式（严格JSON数组，只输出JSON，不要任何分析过程）
[
    {
        "name": "高等数学",
        "day_of_week": 1,
        "period": "1-2节",
        "time_start": "",
        "time_end": "",
        "classroom": "4-B105",
        "teacher": "李老师"
    }
]

⚠️ 重要提醒：
1. 上述思维链分析只在你脑海中进行，不要在输出中体现
2. 直接输出JSON数组，不要任何前缀文字（如"以下是识别结果"）
3. 不要输出markdown代码块标记（不要```json ... ```）
4. 不要输出任何解释性文字
5. 只输出一个纯粹的JSON数组
"""

        payload = {
            "model": "qwen3-vl-plus",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.1
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()

        if result.get("choices"):
            output = result["choices"][0]["message"]["content"]
            logger.info(f"AI识别原始结果: {output[:500]}...")

            output = output.strip()
            if output.startswith("```json"):
                output = output[7:]
            elif output.startswith("```"):
                output = output[3:]

            if output.endswith("```"):
                output = output[:-3]

            output = output.strip()

            try:
                raw_courses = json.loads(output)

                if not isinstance(raw_courses, list):
                    logger.error(f"返回结果不是数组格式: {type(raw_courses)}")
                    return {
                        "status": "error",
                        "error": "返回格式错误",
                        "courses": [],
                        "summary": {}
                    }

                validated_courses = []
                for i, course in enumerate(raw_courses):
                    if isinstance(course, dict):
                        validated = validate_course(course)
                        if validated:
                            validated_courses.append(validated)
                            logger.debug(f"第{i+1}门课程校验通过: {validated['name']}, 置信度: {validated.get('confidence')}")

                logger.info(f"识别完成，共 {len(validated_courses)} 门课程通过校验")

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}, 原始内容: {output[:200]}")
                validated_courses = []

                json_patterns = [
                    r'(\[\s*\{.*\}\s*\])',  # 匹配 [{ ... }]
                    r'(\[\s*\{[\s\S]*\}\s*\])',  # 跨行匹配
                    r'(\[.*\])',  # 通用匹配（兜底）
                ]
                for pattern in json_patterns:
                    json_match = re.search(pattern, output, re.DOTALL)
                    if json_match:
                        try:
                            raw_courses = json.loads(json_match.group(1))
                            for course in raw_courses:
                                if isinstance(course, dict):
                                    validated = validate_course(course)
                                    if validated:
                                        validated_courses.append(validated)
                            if validated_courses:
                                logger.info(f"正则提取 JSON，{len(validated_courses)} 门课程通过校验")
                                break
                        except json.JSONDecodeError:
                            continue

            if not validated_courses:
                return {
                    "status": "error",
                    "error": "未能识别出课程",
                    "courses": [],
                    "summary": {}
                }

            business_check = validate_business_rules(validated_courses)
            confirmation = mark_for_confirmation(validated_courses)

            status = "success"
            if confirmation["summary"]["needs_fix"] > 0:
                status = "needs_review"
            elif confirmation["summary"]["needs_review"] > 0:
                status = "needs_review"

            return {
                "status": status,
                "courses": validated_courses,
                "summary": confirmation["summary"],
                "violations": business_check["violations"],
                "low_confidence": business_check["low_confidence"]
            }

        else:
            logger.error(f"API调用失败: {result}")
            return {
                "status": "error",
                "error": "API调用失败",
                "courses": [],
                "summary": {}
            }

    except Exception as e:
        logger.error(f"图片识别失败: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "courses": [],
            "summary": {}
        }


def parse_course_from_text(text: str) -> List[dict]:
    """从识别文本中解析课程信息"""
    courses = []

    try:
        data = json.loads(text)
        if isinstance(data, list):
            for i, course in enumerate(data):
                if isinstance(course, dict):
                    validated = validate_course(course)
                    if validated:
                        courses.append(validated)
        return courses
    except json.JSONDecodeError:
        logger.error(f"JSON解析失败，原始响应: {text}")
        return []
