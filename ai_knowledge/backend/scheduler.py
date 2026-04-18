"""
定时任务调度器
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Dict, List, Optional
import time

# 初始化调度器（纯内存版，不需要 Redis）
scheduler = None

class DataUpdater:
    """数据更新器"""
    
    @staticmethod
    def update_jobs_only():
        """仅更新职位数据"""
        print(f"[{datetime.now().isoformat()}] 开始更新职位数据...")
        try:
            from scraper import JobScraper
            from data_cleaner import DataCleaner, DataEnricher
            from knowledge_base import get_course_db

            scraper = JobScraper()
            cleaner = DataCleaner()

            majors = ["Java", "Python", "前端", "算法", "大数据", "人工智能"]
            all_jobs = []

            for major in majors:
                jobs = scraper.scrape_jobs(major, limit=30)
                cleaned_jobs = cleaner.clean_job_data(jobs)
                enriched_jobs = DataEnricher.enrich_job_with_trends(cleaned_jobs)
                all_jobs.extend(enriched_jobs)

            # 去重
            all_jobs = DataCleaner.remove_duplicates(all_jobs, ['title', 'company'])

            db = get_course_db()
            count = db.insert_jobs(all_jobs)
            
            # 添加到向量数据库
            from vector_db import get_vector_db
            vector_db = get_vector_db()
            vector_db.add_jobs(all_jobs)
            
            print(f"职位数据更新完成: 新增 {count} 条")
        except Exception as e:
            print(f"职位数据更新失败: {e}")

    @staticmethod
    def update_exams_only():
        """仅更新考研数据"""
        print(f"[{datetime.now().isoformat()}] 开始更新考研数据...")
        try:
            from scraper import ExamScraper
            from data_cleaner import DataCleaner, DataEnricher
            from knowledge_base import get_course_db

            scraper = ExamScraper()
            cleaner = DataCleaner()

            majors = ["计算机", "人工智能", "软件工程", "数据科学"]
            all_exams = []

            for major in majors:
                exams = scraper.scrape_exam_info(major, limit=20)
                cleaned_exams = cleaner.clean_exam_data(exams)
                enriched_exams = DataEnricher.enrich_exam_with_difficulty(cleaned_exams)
                all_exams.extend(enriched_exams)

            db = get_course_db()
            count = db.insert_exams(all_exams)
            
            # 添加到向量数据库
            from vector_db import get_vector_db
            vector_db = get_vector_db()
            vector_db.add_exams(all_exams)
            
            print(f"考研数据更新完成: 新增 {count} 条")
        except Exception as e:
            print(f"考研数据更新失败: {e}")

    @staticmethod
    def update_civil_only():
        """仅更新考公数据"""
        print(f"[{datetime.now().isoformat()}] 开始更新考公数据...")
        try:
            from scraper import CivilExamScraper
            from data_cleaner import DataCleaner
            from knowledge_base import get_course_db

            scraper = CivilExamScraper()
            cleaner = DataCleaner()

            civil_info = scraper.scrape_civil_exam_info(limit=50)
            cleaned_info = cleaner.clean_civil_data(civil_info)

            db = get_course_db()
            count = db.insert_civil_exams(cleaned_info)
            
            # 添加到向量数据库
            from vector_db import get_vector_db
            vector_db = get_vector_db()
            vector_db.add_civil_exams(cleaned_info)
            
            print(f"考公数据更新完成: 新增 {count} 条")
        except Exception as e:
            print(f"考公数据更新失败: {e}")

    @staticmethod
    def update_all():
        """更新所有数据"""
        DataUpdater.update_jobs_only()
        DataUpdater.update_exams_only()
        DataUpdater.update_civil_only()

    @staticmethod
    def generate_graphs_only():
        """仅生成知识图谱"""
        print(f"[{datetime.now().isoformat()}] 开始生成知识图谱...")
        try:
            from knowledge_base import get_course_db
            from main import generate_plan_with_llm

            # 生成常见专业的知识图谱
            common_majors = ["计算机科学", "人工智能", "软件工程", "数据科学", "金融学", "经济学", "工商管理", "会计学"]
            goals = ["就业", "考研", "考公"]

            db = get_course_db()
            count = 0

            for major in common_majors:
                for goal in goals:
                    try:
                        # 生成知识图谱
                        result = generate_plan_with_llm(major, goal)
                        plan_dict = result.dict()

                        # 保存到数据库
                        db.save_plan_template(major, goal, plan_dict)
                        count += 1
                        print(f"生成知识图谱成功: {major} - {goal}")
                    except Exception as e:
                        print(f"生成知识图谱失败 {major} - {goal}: {e}")

            print(f"知识图谱生成完成: 共生成 {count} 个")
        except Exception as e:
            print(f"知识图谱生成失败: {e}")

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
        self._register_tasks()
    
    def _register_tasks(self):
        """注册任务"""
        # 定义任务配置
        tasks = [
            {
                "id": "weekly_update_jobs",
                "name": "每周更新职位数据",
                "func": self._update_job_data,
                "trigger": "cron",
                "day_of_week": "mon",
                "hour": 2,
                "minute": 0
            },
            {
                "id": "weekly_update_exams",
                "name": "每周更新考研数据",
                "func": self._update_exam_data,
                "trigger": "cron",
                "day_of_week": "mon",
                "hour": 3,
                "minute": 0
            },
            {
                "id": "weekly_generate_knowledge_graphs",
                "name": "每周生成知识图谱",
                "func": self._generate_knowledge_graphs,
                "trigger": "cron",
                "day_of_week": "mon",
                "hour": 4,
                "minute": 0
            },
            {
                "id": "monthly_clean_old_data",
                "name": "每月清理旧数据",
                "func": self._clean_old_data,
                "trigger": "cron",
                "day": 1,
                "hour": 1,
                "minute": 0
            }
        ]
        
        # 添加任务
        for task_config in tasks:
            task_id = task_config["id"]
            trigger = self._create_trigger(task_config)
            
            job = self.scheduler.add_job(
                func=task_config["func"],
                trigger=trigger,
                id=task_id,
                name=task_config["name"],
                replace_existing=True
            )

            # 尝试获取下次运行时间，兼容不同版本的APScheduler
            next_run_time = None
            try:
                next_run_time = job.next_run_time
            except AttributeError:
                # 对于新版本的APScheduler，可能使用不同的属性或方法
                pass
            
            self.jobs[task_id] = {
                "name": task_config["name"],
                "next_run": next_run_time
            }
            print(f"[调度器] 任务已添加: {task_config['name']}, 下次执行: {next_run_time}")
    
    def _create_trigger(self, task_config: Dict):
        """创建触发器"""
        trigger_type = task_config.get("trigger", "interval")

        if trigger_type == "interval":
            return IntervalTrigger(
                weeks=task_config.get("weeks", 1),
                hours=task_config.get("hours", 0),
                minutes=task_config.get("minutes", 0)
            )
        elif trigger_type == "cron":
            return CronTrigger(
                day_of_week=task_config.get("day_of_week"),
                day=task_config.get("day"),
                month=task_config.get("month"),
                hour=task_config.get("hour", 0),
                minute=task_config.get("minute", 0)
            )
        else:
            return IntervalTrigger(weeks=1)
    
    def start(self):
        """启动调度器"""
        self.scheduler.start()
        print("[调度器] 调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        print("[调度器] 调度器已停止")
    
    def get_task_status(self) -> List[Dict]:
        """获取所有任务状态"""
        status = []
        for job in self.scheduler.get_jobs():
            # 尝试获取下次运行时间，兼容不同版本的APScheduler
            next_run_time = None
            try:
                next_run_time = job.next_run_time
                next_run_str = next_run_time.isoformat() if next_run_time else None
            except AttributeError:
                next_run_str = None
            
            # 尝试获取pending状态，兼容不同版本的APScheduler
            pending = False
            try:
                pending = job.pending
            except AttributeError:
                pass
            
            status.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run_str,
                "pending": pending
            })
        return status
    
    def run_now(self, task_id: str):
        """立即执行指定任务"""
        job = self.scheduler.get_job(task_id)
        if job:
            job.modify(next_run_time=datetime.now())
            print(f"[调度器] 任务 {task_id} 已设置为立即执行")
        else:
            print(f"[调度器] 任务 {task_id} 不存在")
    
    @staticmethod
    def _update_job_data():
        """更新职位数据"""
        DataUpdater.update_jobs_only()
    
    @staticmethod
    def _update_exam_data():
        """更新考研数据"""
        DataUpdater.update_exams_only()
    
    @staticmethod
    def _generate_knowledge_graphs():
        """生成知识图谱"""
        DataUpdater.generate_graphs_only()
    
    @staticmethod
    def _clean_old_data():
        """清理旧数据"""
        print(f"[{datetime.now().isoformat()}] 开始清理旧数据...")
        try:
            from knowledge_base import get_course_db
            db = get_course_db()
            db.clear_old_data(days=30)
            print("旧数据清理完成")
        except Exception as e:
            print(f"清理旧数据失败: {e}")

# 全局调度器实例
task_scheduler = None

def get_scheduler() -> TaskScheduler:
    """获取任务调度器实例"""
    global task_scheduler
    if task_scheduler is None:
        task_scheduler = TaskScheduler()
    return task_scheduler

if __name__ == "__main__":
    # 测试调度器
    sched = get_scheduler()
    sched.start()
    
    # 打印任务状态
    print("任务状态:")
    for task in sched.get_task_status():
        print(f"- {task['name']}: {task['next_run']}")
    
    # 运行一段时间后停止
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sched.stop()
        print("调度器已停止")
