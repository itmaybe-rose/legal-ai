"""学习计划相关 API"""
from fastapi import APIRouter, Form, HTTPException
from typing import Optional, Dict, Any
import json
from utils.logger import logger

router = APIRouter()

# 全局缓存
PLAN_CACHE = {}


def get_cached_plan(major: str, goal: str) -> Optional[dict]:
    """获取缓存的计划"""
    return PLAN_CACHE.get(f"{major}_{goal}")


def cache_plan(major: str, goal: str, plan: dict):
    """缓存计划"""
    PLAN_CACHE[f"{major}_{goal}"] = plan


 


@router.post("/api/generate_plan")
async def create_plan(major: str = Form(...), goal: str = Form(...), job: Optional[str] = Form(None)):
    """生成学习计划"""
    try:
        if not major or not goal:
            raise HTTPException(status_code=400, detail="参数缺失")
        
        # 转换 goal 参数：将前端的英文转换为中文
        goal_map = {
            "job": "就业",
            "study": "考研",
            "exam": "考公",
            "startup": "创业"
        }
        goal_zh = goal_map.get(goal, goal)
        
        # 1. 尝试从缓存获取
        cached_plan = get_cached_plan(major, goal)
        if cached_plan:
            logger.info(f"使用缓存方案: {major} - {goal}")
            return cached_plan
        
        # 2. 尝试从预设方案获取
        plan_key = f"{major}_{goal}"
        if plan_key in PRESET_PLANS:
            cache_plan(major, goal, PRESET_PLANS[plan_key])
            return PRESET_PLANS[plan_key]
        
        # 3. 从数据库获取预生成的模板
        try:
            from knowledge_base import get_course_db
            db = get_course_db()
            template_plan = db.get_plan_template(major, goal_zh)
            
            if template_plan:
                logger.info(f"使用预生成方案: {major} - {goal_zh}")
                cache_plan(major, goal, template_plan)
                return template_plan
        except Exception as e:
            logger.error(f"数据库查询失败: {e}")
        
        # 4. 从向量数据库检索相关信息
        rag_info = []
        try:
            from vector_db import get_vector_db
            vector_db = get_vector_db()
            rag_query = f"{major} 专业 {goal_zh} 方向"
            rag_results = vector_db.search(rag_query, top_k=3)
            rag_info = rag_results
            logger.info(f"向量数据库检索到 {len(rag_info)} 条相关信息")
        except Exception as e:
            logger.error(f"向量数据库检索失败: {e}")
        
        # 5. 从数据库检索职位数据（如果是就业目标）
        job_market_data = []
        if goal_zh == "就业":
            try:
                from knowledge_base import get_course_db
                db = get_course_db()
                job_market_data = db.search_jobs(major, limit=5)
                logger.info(f"数据库检索到 {len(job_market_data)} 条职位数据")
                
                # 转换职位数据格式
                formatted_jobs = []
                for job_item in job_market_data:
                    skills = []
                    if job_item.get('skills'):
                        try:
                            skills = json.loads(job_item['skills'])
                        except:
                            skills = []
                    
                    formatted_jobs.append({
                        "name": job_item.get('title', ''),
                        "salary": job_item.get('salary_raw', ''),
                        "skills": skills,
                        "is_core": True
                    })
                job_market_data = formatted_jobs
            except Exception as e:
                logger.error(f"职位数据检索失败: {e}")
        
        # 6. 兜底：调用大模型生成（如果有配置的话）
        try:
            from main_old import generate_plan_with_llm
            logger.info(f"调用大模型生成方案: {major} - {goal_zh}")
            result = generate_plan_with_llm(major, goal_zh, job)
            plan_dict = result.dict()
            
            # 如果大模型返回的职位数据为空，使用数据库中的数据
            if not plan_dict.get('job_market') and job_market_data:
                plan_dict['job_market'] = job_market_data
            
            cache_plan(major, goal, plan_dict)
            return plan_dict
        except Exception as e:
            logger.warning(f"大模型调用失败，使用默认方案: {e}")
        
        # 7. 返回默认学习路径（当所有方法都失败时）
        default_plan = {
            "skill_tree": [
                {"id": "1", "label": f"{major}基础", "level": "core", "description": f"{major}专业基础知识"},
                {"id": "2", "label": f"{major}核心课程", "level": "core", "description": f"{major}专业核心课程"},
                {"id": "3", "label": f"{major}进阶技能", "level": "high", "description": f"{major}进阶技能学习"},
                {"id": "4", "label": "实践项目", "level": "high", "description": "实际项目经验"},
                {"id": "5", "label": "行业前沿", "level": "low", "description": "了解行业最新动态"},
            ],
            "resource_recommendations": [],
            "job_market": job_market_data if job_market_data else [],
        }
        
        cache_plan(major, goal, default_plan)
        return default_plan
        
    except Exception as e:
        logger.error(f"错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


 