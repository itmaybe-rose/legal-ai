"""AI图片识别服务 - 用于识别课程表图片"""
import os
import base64
import json
import requests
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")


def recognize_schedule_image(image_path: str) -> list:
    """
    使用阿里云通义千问视觉模型(qwen3-vl-plus)识别课程表图片
    
    :param image_path: 图片文件路径
    :return: 识别出的课程列表
    """
    if not DASHSCOPE_API_KEY:
        logger.warning("未配置DASHSCOPE_API_KEY")
        return []
     
    try:
        # 读取图片并编码为base64
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # 使用通义千问视觉模型API端点
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
        }
        
        prompt = """请识别这张课程表图片中的所有课程信息，包括：
        1. 课程名称
        2. 星期几（1-7，周一为1）
        3. 上课节次（如"1-2节"或"3-4节"）
        4. 上课时间（开始时间和结束时间）
        5. 教室位置
        6. 授课教师（如果有的话）
        
        请以JSON格式输出，格式如下：
        [
            {"name": "课程名称", "day_of_week": 1, "period": "1-2节", "time_start": "08:00", "time_end": "09:40", "classroom": "教学楼A301", "teacher": "张老师"},
            ...
        ]
        
        如果某个信息无法识别，请留空字符串或null。
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
            
            # 去除Markdown代码块标记
            output = output.strip()
            if output.startswith("```json"):
                output = output[7:]  # 去除 ```json
            elif output.startswith("```"):
                output = output[3:]  # 去除 ```
            
            if output.endswith("```"):
                output = output[:-3]  # 去除末尾的 ```
            
            output = output.strip()
            
            # 尝试解析JSON
            try:
                courses = json.loads(output)
                logger.info(f"成功解析 {len(courses)} 门课程")
                return courses
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                logger.debug(f"清理后的内容: {output[:200]}...")
                return []
        else:
            logger.error(f"API调用失败: {result}")
            return []
            
    except Exception as e:
        logger.error(f"图片识别失败: {str(e)}")
        return []


 


def parse_course_from_text(text: str) -> list:
    """
    从识别文本中解析课程信息
    
    :param text: AI识别返回的文本
    :return: 课程列表
    """
    courses = []
    
    # 定义颜色列表
    colors = ["#409eff", "#67c23a", "#f56c6c", "#909399", "#e6a23c", "#f78900", "#7232dd", "#3ba272"]
    
    try:
        # 尝试JSON解析
        data = json.loads(text)
        if isinstance(data, list):
            for i, course in enumerate(data):
                if isinstance(course, dict):
                    course_data = {
                        "name": course.get("name", ""),
                        "day_of_week": course.get("day_of_week", 1),
                        "period": course.get("period", ""),
                        "time_start": course.get("time_start", ""),
                        "time_end": course.get("time_end", ""),
                        "classroom": course.get("classroom", ""),
                        "teacher": course.get("teacher", ""),
                        "color": colors[i % len(colors)]
                    }
                    if course_data["name"]:
                        courses.append(course_data)
        return courses
    except json.JSONDecodeError:
        # 如果不是JSON格式，返回空列表
        logger.error(f"JSON解析失败，原始响应: {text}")
        return []
        
