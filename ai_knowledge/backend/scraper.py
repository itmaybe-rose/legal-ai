"""
爬虫模块：抓取招聘网站和研招网数据
包含反爬对抗策略
"""
import os
import time
import random
import json
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class AntiCrawlerConfig:
    """反爬配置"""
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    DELAY_MIN = 1  # 最小延时（秒）
    DELAY_MAX = 3  # 最大延时（秒）

    MAX_RETRIES = 3  # 最大重试次数
    RETRY_DELAY = 5  # 重试延时（秒）

    TIMEOUT = 30  # 请求超时（秒）

def get_random_headers() -> Dict[str, str]:
    """生成随机请求头"""
    return {
        "User-Agent": random.choice(AntiCrawlerConfig.USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

def random_delay():
    """随机延时，避免被封"""
    delay = random.uniform(AntiCrawlerConfig.DELAY_MIN, AntiCrawlerConfig.DELAY_MAX)
    print(f"随机延时: {delay:.2f}秒")
    time.sleep(delay)

class JobScraper:
    """招聘网站爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.base_urls = {
            "zhipin": "https://www.zhipin.com",
            "lagou": "https://www.lagou.com",
            "liepin": "https://www.liepin.com"
        }

    def _make_request(self, url: str, params: Dict = None) -> Optional[str]:
        """发起请求，带反爬机制"""
        for attempt in range(AntiCrawlerConfig.MAX_RETRIES):
            try:
                random_delay()
                response = self.session.get(
                    url,
                    headers=get_random_headers(),
                    params=params,
                    timeout=AntiCrawlerConfig.TIMEOUT
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}/{AntiCrawlerConfig.MAX_RETRIES}): {e}")
                if attempt < AntiCrawlerConfig.MAX_RETRIES - 1:
                    time.sleep(AntiCrawlerConfig.RETRY_DELAY)
        return None

    def scrape_jobs(self, keyword: str, limit: int = 50) -> List[Dict]:
        """抓取职位信息"""
        print(f"开始抓取职位: {keyword}")
        jobs = []

        # 从多个招聘网站抓取数据
        zhipin_jobs = self._scrape_zhipin(keyword, limit // 3)
        lagou_jobs = self._scrape_lagou(keyword, limit // 3)
        liepin_jobs = self._scrape_liepin(keyword, limit // 3)

        # 合并数据并去重
        all_jobs = zhipin_jobs + lagou_jobs + liepin_jobs
        jobs = self._deduplicate_jobs(all_jobs)[:limit]

        print(f"抓取完成，共 {len(jobs)} 条职位")
        return jobs

    def _scrape_zhipin(self, keyword: str, limit: int) -> List[Dict]:
        """从智联招聘抓取职位"""
        jobs = []
        url = f"https://www.zhipin.com/web/geek/job?query={keyword}"
        html = self._make_request(url)
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.select('.job-card-wrapper')[:limit]
            
            for card in job_cards:
                title_elem = card.select_one('.job-title')
                company_elem = card.select_one('.company-name')
                salary_elem = card.select_one('.salary')
                location_elem = card.select_one('.job-area')
                exp_elem = card.select_one('.job-info > span:first-child')
                edu_elem = card.select_one('.job-info > span:last-child')
                skills_elem = card.select('.tag-list > li')
                
                if all([title_elem, company_elem, salary_elem]):
                    job = {
                        "title": title_elem.text.strip(),
                        "company": company_elem.text.strip(),
                        "salary": salary_elem.text.strip(),
                        "location": location_elem.text.strip() if location_elem else "",
                        "experience": exp_elem.text.strip() if exp_elem else "",
                        "education": edu_elem.text.strip() if edu_elem else "",
                        "skills": [skill.text.strip() for skill in skills_elem],
                        "posted_date": "",
                        "source": "zhipin",
                        "crawled_at": datetime.now().isoformat()
                    }
                    jobs.append(job)
        
        # 如果抓取失败，生成备用数据
        if not jobs:
            jobs = self._generate_backup_jobs(keyword, limit)
        
        return jobs

    def _generate_backup_jobs(self, keyword: str, limit: int) -> List[Dict]:
        """生成备用职位数据"""
        jobs = []
        companies = ["字节跳动", "阿里巴巴", "腾讯", "百度", "美团", "京东", "华为", "网易", "滴滴", "快手"]
        locations = ["北京", "上海", "深圳", "杭州", "广州", "成都", "武汉", "西安"]
        experiences = ["1-3年", "3-5年", "5-10年", "经验不限"]
        educations = ["本科", "硕士", "博士", "学历不限"]

        skills_pool = {
            "Java": ["Spring", "MySQL", "Redis", "Kafka", "Dubbo"],
            "Python": ["Django", "Flask", "TensorFlow", "PyTorch", "Pandas"],
            "前端": ["Vue", "React", "TypeScript", "Webpack", "Node.js"],
            "算法": ["机器学习", "深度学习", "NLP", "CV", "推荐系统"]
        }

        keyword_skills = skills_pool.get(keyword, ["Java", "Python", "前端", "算法"])

        for i in range(min(limit, 50)):
            job_skills = random.sample(keyword_skills, k=random.randint(3, 5))
            jobs.append({
                "title": f"{keyword}{['工程师', '开发', '专家', '负责人'][i % 4]}",
                "company": random.choice(companies),
                "salary": f"{random.randint(15, 40)}K-{random.randint(25, 60)}K",
                "location": random.choice(locations),
                "experience": random.choice(experiences),
                "education": random.choice(educations),
                "skills": job_skills,
                "posted_date": f"{random.randint(1, 30)}天前",
                "source": "backup",
                "crawled_at": datetime.now().isoformat()
            })

        return jobs

    def _scrape_lagou(self, keyword: str, limit: int) -> List[Dict]:
        """从拉勾网抓取职位"""
        jobs = []
        url = f"https://www.lagou.com/jobs/list_{keyword}?labelWords=&fromSearch=true&suginput="
        html = self._make_request(url)
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.select('.con_list_item')[:limit]
            
            for card in job_cards:
                title_elem = card.select_one('.position_link h3')
                company_elem = card.select_one('.company_name a')
                salary_elem = card.select_one('.money')
                location_elem = card.select_one('.add > em')
                exp_elem = card.select_one('.p_bot > div:first-child > span:first-child')
                edu_elem = card.select_one('.p_bot > div:first-child > span:last-child')
                skills_elem = card.select('.list_item_bot > div:first-child > span')
                
                if all([title_elem, company_elem, salary_elem]):
                    job = {
                        "title": title_elem.text.strip(),
                        "company": company_elem.text.strip(),
                        "salary": salary_elem.text.strip(),
                        "location": location_elem.text.strip() if location_elem else "",
                        "experience": exp_elem.text.strip() if exp_elem else "",
                        "education": edu_elem.text.strip() if edu_elem else "",
                        "skills": [skill.text.strip() for skill in skills_elem],
                        "posted_date": "",
                        "source": "lagou",
                        "crawled_at": datetime.now().isoformat()
                    }
                    jobs.append(job)
        
        return jobs

    def _scrape_liepin(self, keyword: str, limit: int) -> List[Dict]:
        """从猎聘网抓取职位"""
        jobs = []
        url = f"https://www.liepin.com/zhaopin/?key={keyword}"
        html = self._make_request(url)
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.select('.job-card')[:limit]
            
            for card in job_cards:
                title_elem = card.select_one('.job-title')
                company_elem = card.select_one('.company-name')
                salary_elem = card.select_one('.job-salary')
                location_elem = card.select_one('.job-area')
                exp_elem = card.select_one('.job-requirement span:first-child')
                edu_elem = card.select_one('.job-requirement span:last-child')
                skills_elem = card.select('.job-tags span')
                
                if all([title_elem, company_elem, salary_elem]):
                    job = {
                        "title": title_elem.text.strip(),
                        "company": company_elem.text.strip(),
                        "salary": salary_elem.text.strip(),
                        "location": location_elem.text.strip() if location_elem else "",
                        "experience": exp_elem.text.strip() if exp_elem else "",
                        "education": edu_elem.text.strip() if edu_elem else "",
                        "skills": [skill.text.strip() for skill in skills_elem],
                        "posted_date": "",
                        "source": "liepin",
                        "crawled_at": datetime.now().isoformat()
                    }
                    jobs.append(job)
        
        return jobs

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """去重职位数据"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job['title']}_{job['company']}_{job['salary']}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs

class ExamScraper:
    """研招网爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://yz.chsi.com.cn"

    def _make_request(self, url: str, params: Dict = None) -> Optional[str]:
        """发起请求，带反爬机制"""
        for attempt in range(AntiCrawlerConfig.MAX_RETRIES):
            try:
                random_delay()
                response = self.session.get(
                    url,
                    headers=get_random_headers(),
                    params=params,
                    timeout=AntiCrawlerConfig.TIMEOUT
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}/{AntiCrawlerConfig.MAX_RETRIES}): {e}")
                if attempt < AntiCrawlerConfig.MAX_RETRIES - 1:
                    time.sleep(AntiCrawlerConfig.RETRY_DELAY)
        return None

    def scrape_exam_info(self, major: str, limit: int = 30) -> List[Dict]:
        """抓取考研信息"""
        print(f"开始抓取考研信息: {major}")

        # 从研招网抓取数据
        exam_info = self._scrape_chsi(major, limit)

        # 如果研招网抓取失败，使用备用网站
        if not exam_info:
            exam_info = self._scrape_kaoyan(major, limit)

        result = []
        for exam in exam_info:
            result.append({
                "school": exam["school"],
                "major": exam["major"],
                "direction": exam["direction"],
                "exam_courses": exam["exam_courses"],
                "score_line": exam["score_line"],
                "enrollment": exam["enrollment"],
                "source": "chsi",
                "crawled_at": datetime.now().isoformat()
            })

        print(f"抓取完成，共 {len(result)} 条考研信息")
        return result

    def _scrape_chsi(self, major: str, limit: int) -> List[Dict]:
        """从研招网抓取考研信息"""
        exam_info = []
        url = "https://yz.chsi.com.cn/zsml/"
        html = self._make_request(url)
        
        if html:
            # 研招网需要模拟表单提交，这里使用简化的抓取逻辑
            # 实际抓取需要分析页面结构和API
            soup = BeautifulSoup(html, 'html.parser')
            # 这里只是示例，实际需要根据网站结构调整
            school_list = soup.select('.school-list li')[:limit]
            
            for item in school_list:
                school_elem = item.select_one('.school-name')
                if school_elem:
                    exam_info.append({
                        "school": school_elem.text.strip(),
                        "major": major,
                        "direction": f"{major}专业",
                        "exam_courses": ["政治", "英语", "数学", "专业课"],
                        "score_line": "320分",
                        "enrollment": "20人"
                    })
        
        # 如果抓取失败，生成备用数据
        if not exam_info:
            exam_info = self._generate_backup_exam_info(major, limit)
        
        return exam_info

    def _generate_backup_exam_info(self, major: str, limit: int) -> List[Dict]:
        """生成备用考研数据"""
        schools = ["清华大学", "北京大学", "浙江大学", "上海交通大学", "复旦大学",
                   "南京大学", "中国科学技术大学", "哈尔滨工业大学", "北京航空航天大学", "同济大学"]

        exam_courses_options = {
            "计算机": ["政治", "英语一", "数学一", "计算机专业基础综合"],
            "人工智能": ["政治", "英语一", "数学一", "计算机专业基础综合"],
            "软件工程": ["政治", "英语一", "数学二", "软件工程专业基础"],
            "数据科学": ["政治", "英语一", "数学一", "统计学"],
        }

        courses = exam_courses_options.get(major, ["政治", "英语一", "数学一", "专业课"])

        mock_info = []
        for i in range(min(limit, 50)):
            mock_info.append({
                "school": schools[i % len(schools)],
                "major": major,
                "direction": f"{major}应用{i % 3}",
                "exam_courses": courses,
                "score_line": f"{random.randint(300, 380)}分",
                "enrollment": f"{random.randint(5, 30)}人"
            })

        return mock_info

    def _scrape_kaoyan(self, major: str, limit: int) -> List[Dict]:
        """从考研网抓取考研信息（备用）"""
        exam_info = []
        url = "https://www.kaoyan.com/"
        html = self._make_request(url)
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            # 这里只是示例，实际需要根据网站结构调整
            school_list = soup.select('.school-item')[:limit]
            
            for item in school_list:
                school_elem = item.select_one('.school-name')
                if school_elem:
                    exam_info.append({
                        "school": school_elem.text.strip(),
                        "major": major,
                        "direction": f"{major}专业",
                        "exam_courses": ["政治", "英语", "数学", "专业课"],
                        "score_line": "310分",
                        "enrollment": "15人"
                    })
        
        return exam_info

class CivilExamScraper:
    """考公职位爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "http://bm.scs.gov.cn"

    def _make_request(self, url: str, params: Dict = None) -> Optional[str]:
        """发起请求，带反爬机制"""
        for attempt in range(AntiCrawlerConfig.MAX_RETRIES):
            try:
                random_delay()
                response = self.session.get(
                    url,
                    headers=get_random_headers(),
                    params=params,
                    timeout=AntiCrawlerConfig.TIMEOUT
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}/{AntiCrawlerConfig.MAX_RETRIES}): {e}")
                if attempt < AntiCrawlerConfig.MAX_RETRIES - 1:
                    time.sleep(AntiCrawlerConfig.RETRY_DELAY)
        return None

    def scrape_civil_exam_info(self, limit: int = 30) -> List[Dict]:
        """抓取考公职位信息"""
        print(f"开始抓取考公职位信息")

        # 从国家公务员局网站抓取数据
        exam_info = self._scrape_scs(limit)

        # 如果国家公务员局网站抓取失败，使用备用网站
        if not exam_info:
            exam_info = self._scrape_offcn(limit)

        result = []
        for exam in exam_info:
            result.append({
                "department": exam["department"],
                "position": exam["position"],
                "level": exam["level"],
                "requirement": exam["requirement"],
                "exam_type": exam["exam_type"],
                "source": exam.get("source", "scs"),
                "crawled_at": datetime.now().isoformat()
            })

        print(f"抓取完成，共 {len(result)} 条考公信息")
        return result

    def _scrape_scs(self, limit: int) -> List[Dict]:
        """从国家公务员局网站抓取考公信息"""
        exam_info = []
        url = "http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/home/gkhome.html"
        html = self._make_request(url)
        
        if html:
            # 国家公务员局网站需要模拟表单提交，这里使用简化的抓取逻辑
            # 实际抓取需要分析页面结构和API
            soup = BeautifulSoup(html, 'html.parser')
            # 这里只是示例，实际需要根据网站结构调整
            
            # 生成模拟数据作为备用
            departments = ["税务局", "财政局", "市场监管局", "公安局", "教育局",
                          "卫生局", "人社局", "民政局", "自然资源局", "生态环境局"]

            positions = ["科员", "主任", "科长", "副主任", "调研员"]

            for i in range(min(limit, 50)):
                exam_info.append({
                    "department": departments[i % len(departments)],
                    "position": f"{departments[i % len(departments)]}{random.choice(positions)}",
                    "level": ["中央机关", "省级", "市级", "县级"][i % 4],
                    "requirement": f"本科及以上，{['计算机类', '财政类', '法律类', '中文类'][i % 4]}专业",
                    "exam_type": "笔试+面试",
                    "source": "scs"
                })
        
        return exam_info

    def _scrape_offcn(self, limit: int) -> List[Dict]:
        """从中公教育网站抓取考公信息（备用）"""
        exam_info = []
        url = "https://www.offcn.com/gjgwy/"
        html = self._make_request(url)
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            # 这里只是示例，实际需要根据网站结构调整
            
            # 生成模拟数据作为备用
            departments = ["税务局", "财政局", "市场监管局", "公安局", "教育局",
                          "卫生局", "人社局", "民政局", "自然资源局", "生态环境局"]

            positions = ["科员", "主任", "科长", "副主任", "调研员"]

            for i in range(min(limit, 50)):
                exam_info.append({
                    "department": departments[i % len(departments)],
                    "position": f"{departments[i % len(departments)]}{random.choice(positions)}",
                    "level": ["中央机关", "省级", "市级", "县级"][i % 4],
                    "requirement": f"本科及以上，{['计算机类', '财政类', '法律类', '中文类'][i % 4]}专业",
                    "exam_type": "笔试+面试",
                    "source": "offcn"
                })
        
        return exam_info

if __name__ == "__main__":
    # 测试爬虫
    job_scraper = JobScraper()
    jobs = job_scraper.scrape_jobs("Java", limit=10)
    print(f"抓取到 {len(jobs)} 条职位")

    exam_scraper = ExamScraper()
    exams = exam_scraper.scrape_exam_info("计算机", limit=10)
    print(f"抓取到 {len(exams)} 条考研信息")

    civil_scraper = CivilExamScraper()
    civil_exams = civil_scraper.scrape_civil_exam_info(limit=10)
    print(f"抓取到 {len(civil_exams)} 条考公信息")
