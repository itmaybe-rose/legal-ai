"""
数据清洗模块：将原始数据转为结构化JSON
使用Pandas和正则表达式进行数据清洗
"""
import os
import re
import json
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

@staticmethod
def remove_duplicates(data: List[Dict], keys: List[str]) -> List[Dict]:
    """基于指定字段去重"""
    seen = set()
    unique_data = []
    for item in data:
        # 生成唯一键，例如基于 职位名+公司名
        key = tuple(item.get(k, '') for k in keys)
        if key not in seen:
            seen.add(key)
            unique_data.append(item)
    return unique_data

# 在 scheduler.py 中调用
# all_jobs = DataCleaner.remove_duplicates(all_jobs, ['title', 'company'])

class DataCleaner:
    """数据清洗器"""

    @staticmethod
    def clean_job_data(jobs: List[Dict]) -> List[Dict]:
        """清洗职位数据"""
        cleaned = []

        for job in jobs:
            cleaned_job = {
                "title": DataCleaner._clean_text(job.get("title", "")),
                "company": DataCleaner._clean_text(job.get("company", "")),
                "salary": DataCleaner._parse_salary(job.get("salary", "")),
                "location": DataCleaner._clean_location(job.get("location", "")),
                "experience": DataCleaner._clean_text(job.get("experience", "")),
                "education": DataCleaner._clean_text(job.get("education", "")),
                "skills": DataCleaner._clean_skills(job.get("skills", [])),
                "posted_date": DataCleaner._clean_text(job.get("posted_date", "")),
                "source": job.get("source", ""),
                "crawled_at": job.get("crawled_at", datetime.now().isoformat())
            }
            cleaned.append(cleaned_job)

        return cleaned

    @staticmethod
    def clean_exam_data(exams: List[Dict]) -> List[Dict]:
        """清洗考研数据"""
        cleaned = []

        for exam in exams:
            cleaned_exam = {
                "school": DataCleaner._clean_text(exam.get("school", "")),
                "major": DataCleaner._clean_text(exam.get("major", "")),
                "direction": DataCleaner._clean_text(exam.get("direction", "")),
                "exam_courses": DataCleaner._clean_courses(exam.get("exam_courses", [])),
                "score_line": DataCleaner._parse_score_line(exam.get("score_line", "")),
                "enrollment": DataCleaner._parse_enrollment(exam.get("enrollment", "")),
                "source": exam.get("source", ""),
                "crawled_at": exam.get("crawled_at", datetime.now().isoformat())
            }
            cleaned.append(cleaned_exam)

        return cleaned

    @staticmethod
    def clean_civil_data(civil_info: List[Dict]) -> List[Dict]:
        """清洗考公数据"""
        cleaned = []

        for info in civil_info:
            cleaned_info = {
                "department": DataCleaner._clean_text(info.get("department", "")),
                "position": DataCleaner._clean_text(info.get("position", "")),
                "level": DataCleaner._clean_text(info.get("level", "")),
                "requirement": DataCleaner._clean_text(info.get("requirement", "")),
                "exam_type": DataCleaner._clean_text(info.get("exam_type", "")),
                "source": info.get("source", ""),
                "crawled_at": info.get("crawled_at", datetime.now().isoformat())
            }
            cleaned.append(cleaned_info)

        return cleaned

    @staticmethod
    def _clean_text(text: str) -> str:
        """清洗文本，去除多余空白和特殊字符"""
        if not text:
            return ""
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 去除特殊字符（保留中文、英文、数字、常用标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s,，。、：；""''（）()]', '', text)
        return text.strip()

    @staticmethod
    def _clean_location(location: str) -> str:
        """清洗地区信息"""
        location = DataCleaner._clean_text(location)
        # 标准化城市名称
        city_mapping = {
            "北京市": "北京",
            "上海市": "上海",
            "深圳市": "深圳",
            "广州市": "广州",
            "杭州市": "杭州",
            "成都市": "成都",
            "武汉市": "武汉",
            "西安市": "西安",
            "南京市": "南京",
            "重庆市": "重庆"
        }
        for full, short in city_mapping.items():
            if full in location:
                return short
        return location

    @staticmethod
    def _parse_salary(salary: str) -> Dict[str, Any]:
        """解析薪资字符串"""
        # 匹配格式: 15K-30K, 15k-30k, 15000-30000
        pattern = r'(\d+)[kK]?-(\d+)[kK]?'
        match = re.search(pattern, salary, re.IGNORECASE)

        if match:
            min_salary = int(match.group(1))
            max_salary = int(match.group(2))
            # 如果是K单位，转换为实际薪资
            if 'k' in salary.lower():
                min_salary *= 1000
                max_salary *= 1000
            return {
                "min": min_salary,
                "max": max_salary,
                "raw": salary
            }

        # 尝试匹配其他格式
        pattern2 = r'(\d+)-(\d+)'
        match2 = re.search(pattern2, salary)
        if match2:
            return {
                "min": int(match2.group(1)),
                "max": int(match2.group(2)),
                "raw": salary
            }

        return {"min": 0, "max": 0, "raw": salary}

    @staticmethod
    def _clean_skills(skills: List[str]) -> List[str]:
        """清洗技能列表"""
        if not skills:
            return []

        cleaned = []
        for skill in skills:
            skill = DataCleaner._clean_text(skill)
            if skill and len(skill) > 0:
                cleaned.append(skill)

        return list(set(cleaned))  # 去重

    @staticmethod
    def _clean_courses(courses: List[str]) -> List[str]:
        """清洗考试科目"""
        if not courses:
            return []

        cleaned = []
        for course in courses:
            course = DataCleaner._clean_text(course)
            # 标准化科目名称
            course_mapping = {
                "思想政治理论": "政治",
                "英语（一）": "英语一",
                "英语（二）": "英语二",
                "业务课一": "专业课一",
                "业务课二": "专业课二"
            }
            course = course_mapping.get(course, course)
            if course:
                cleaned.append(course)

        return cleaned

    @staticmethod
    def _parse_score_line(score_line: str) -> Dict[str, Any]:
        """解析分数线"""
        # 匹配格式: 300分, 300-350分
        pattern = r'(\d+)(?:-(\d+))?分?'
        match = re.search(pattern, score_line)

        if match:
            min_score = int(match.group(1))
            max_score = int(match.group(2)) if match.group(2) else min_score
            return {
                "min": min_score,
                "max": max_score,
                "raw": score_line
            }

        return {"min": 0, "max": 0, "raw": score_line}

    @staticmethod
    def _parse_enrollment(enrollment: str) -> Dict[str, Any]:
        """解析招生人数"""
        # 匹配格式: 30人, 20-30人
        pattern = r'(\d+)(?:-(\d+))?人'
        match = re.search(pattern, enrollment)

        if match:
            min_num = int(match.group(1))
            max_num = int(match.group(2)) if match.group(2) else min_num
            return {
                "min": min_num,
                "max": max_num,
                "raw": enrollment
            }

        return {"min": 0, "max": 0, "raw": enrollment}

    @staticmethod
    def to_dataframe(data: List[Dict]) -> pd.DataFrame:
        """转换为DataFrame便于分析"""
        return pd.DataFrame(data)

    @staticmethod
    def to_json(data: List[Dict], filepath: str) -> None:
        """保存为JSON文件"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_json(filepath: str) -> List[Dict]:
        """从JSON文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

class DataEnricher:
    """数据增强器"""

    @staticmethod
    def enrich_job_with_trends(jobs: List[Dict]) -> List[Dict]:
        """根据薪资水平添加趋势标签"""
        for job in jobs:
            salary_min = job.get("salary", {}).get("min", 0)
            salary_max = job.get("salary", {}).get("max", 0)
            avg_salary = (salary_min + salary_max) / 2

            if avg_salary >= 35000:
                job["trend"] = "热门"
            elif avg_salary >= 20000:
                job["trend"] = "平稳"
            else:
                job["trend"] = "一般"

        return jobs

    @staticmethod
    def enrich_exam_with_difficulty(exams: List[Dict]) -> List[Dict]:
        """根据分数线添加难度标签"""
        for exam in exams:
            score = exam.get("score_line", {}).get("min", 0)

            if score >= 360:
                exam["difficulty"] = "困难"
            elif score >= 300:
                exam["difficulty"] = "中等"
            else:
                exam["difficulty"] = "较易"

        return exams

if __name__ == "__main__":
    # 测试数据清洗
    test_jobs = [
        {
            "title": "  Java \n\n  工程师  ",
            "company": "字节跳动",
            "salary": "20K-40K",
            "location": "北京市朝阳区",
            "experience": "3-5年",
            "education": "本科",
            "skills": ["Java", "Spring", "  MySQL  "],
            "posted_date": "3天前",
            "source": "zhipin"
        }
    ]

    cleaner = DataCleaner()
    cleaned = cleaner.clean_job_data(test_jobs)
    print("清洗后的数据:")
    print(json.dumps(cleaned, ensure_ascii=False, indent=2))
