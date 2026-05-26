"""学习计划相关 API"""
from fastapi import APIRouter, Form, HTTPException
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timedelta
from utils.logger import logger
from utils.response import success
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import os

router = APIRouter()

# --- Pydantic 模型定义 ---
class SkillNode(BaseModel):
    id: str = Field(description="唯一ID，例如 '1', '1-1'")
    label: str = Field(description="技能或知识点名称")
    level: str = Field(description="重要程度: core(核心必学/高薪), high(进阶), low(了解)")
    mastered: bool = Field(default=False, description="默认未掌握")
    children: Optional[List['SkillNode']] = Field(default=[], description="子技能节点")

class LearningResource(BaseModel):
    title: str = Field(description="资源标题")
    difficulty: str = Field(description="难度分级: 青铜, 黄金, 王者")
    source: str = Field(description="来源平台，如 Bilibili, GitHub, 官方文档")
    desc: str = Field(description="推荐理由和简介")
    job_relevance: str = Field(description="对应岗位，如 '后端开发工程师'")

class JobMarketData(BaseModel):
    name: str = Field(description="岗位名称")
    salary: str = Field(description="薪资范围")
    skills: List[str] = Field(description="关键技能列表")
    is_core: bool = Field(description="是否核心岗位")

class CareerPlanResponse(BaseModel):
    summary: str = Field(description="针对该目标的简短职业规划建议")
    skill_tree: List[SkillNode] = Field(description="技能树结构")
    resources: List[LearningResource] = Field(description="推荐的学习资源列表")
    job_market: Optional[List[JobMarketData]] = Field(default=[], description="就业风向标数据")

SkillNode.model_rebuild()

# 初始化大模型
llm = ChatOpenAI(
    model="qwen-max", 
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.3,
    max_tokens=800,
    top_p=0.8
)

def generate_plan_with_llm(major: str, goal: str, job: Optional[str] = None) -> CareerPlanResponse:
    """
    生成学习计划的核心函数
    :param major: 专业名称
    :param goal: 学习目标（就业/考研/创业/考公）
    :param job: 目标岗位（可选）
    :return: 结构化的学习计划响应
    """
    parser = PydanticOutputParser(pydantic_object=CareerPlanResponse)

    # 使用 RAG 检索相关信息
    from vector_db import get_vector_db
    vector_db = get_vector_db()
    rag_query = f"{major} 专业 {goal} 方向学习计划"
    relevant_info = vector_db.search(rag_query, top_k=3)

    rag_info = "\n参考学习计划：\n"
    if relevant_info:
        for i, info in enumerate(relevant_info, 1):
            rag_info += f"{i}. {info}\n"
    else:
        rag_info = "\n参考学习计划：无（首次生成）\n"

    goal_template_map = {
        "就业": "你是一位专业的职业规划导师，请根据用户的专业背景和目标岗位，生成一份详细的学习路径，包括核心技能、推荐课程和就业建议。",
        "考研": "你是一位教育专家，请根据用户的专业背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "创业": "你是一位创业导师，请根据用户的专业背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。",
        "考公": "你是一位考公指导专家，请根据用户的专业背景和目标岗位，生成一份详细的备考学习路径，包括考试科目、复习计划和上岸建议。"
    }
    domain_template = goal_template_map.get(goal, goal_template_map["就业"])

    prompt_template = """
    {domain_template}

    用户背景：
    - 专业/领域: {major}
    - 学习目标: {goal}
    - 目标岗位: {job}

    参考信息：
    {rag_info}

    请根据用户的专业、目标、岗位和参考信息，生成一份定制化的学习路径。

    要求：
    1. **技能树构建**:
       - 必须与用户的专业领域相关，不要生成与专业无关的技能。
       - 如果是"就业"，侧重实战技能、行业需求和面试高频题。
       - 如果是"考研"，侧重专业基础、考试重点和复习方法。
       - 如果是"创业"，侧重商业思维、市场需求和创新能力。
       - 如果是"考公"，侧重行测、申论和专业科目。
       - 标记 `level`: "core" 代表核心技能，"high" 代表进阶，"low" 代表了解。
    2. **资源推荐**:
       - 必须包含具体的学习资源，如书籍、视频课程、在线平台等。
       - 推荐与用户专业和目标相关的资源。
       - 按照入门→进阶→实战分级。
    3. **就业风向标**:
       - 如果是"就业"，请生成至少5个与该专业相关的热门岗位。
       - 每个岗位包含：岗位名称、薪资范围、关键技能列表、是否核心岗位。
    4. **格式**: 必须严格遵守 Pydantic 定义的 JSON 格式。

    {format_instructions}
    """

    prompt = ChatPromptTemplate.from_template(template=prompt_template)
    chain = prompt | llm | parser

    try:
        response = chain.invoke({
            "major": major,
            "goal": goal,
            "job": job if job else "未指定",
            "domain_template": domain_template,
            "rag_info": rag_info,
            "format_instructions": parser.get_format_instructions()
        })
        return response
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        raise HTTPException(status_code=500, detail="大模型生成失败")

# 全局缓存
PLAN_CACHE = {}

# 学习计划过期时间（天）
PLAN_EXPIRE_DAYS = 365


def get_cached_plan(major: str, goal: str) -> Optional[dict]:
    """获取缓存的计划"""
    cache_key = f"{major}_{goal}"
    cached = PLAN_CACHE.get(cache_key)
    
    if cached:
        # 检查是否过期
        cached_time = cached.get("_cached_time")
        if cached_time:
            cached_date = datetime.fromisoformat(cached_time)
            if datetime.now() - cached_date > timedelta(days=PLAN_EXPIRE_DAYS):
                logger.info(f"缓存已过期: {cache_key}")
                return None
    
    return cached


def cache_plan(major: str, goal: str, plan: dict):
    """缓存计划（带时间戳）"""
    cache_key = f"{major}_{goal}"
    plan["_cached_time"] = datetime.now().isoformat()
    PLAN_CACHE[cache_key] = plan


 


@router.post("/api/generate_plan")
async def create_plan(
    major: str = Form(...), 
    goal: str = Form(...), 
    job: Optional[str] = Form(None),
    force_refresh: bool = Form(False)  # 强制刷新
):
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
        
         
        
        # 1. 尝试从缓存获取（如果非强制刷新）
        if not force_refresh:
            cached_plan = get_cached_plan(major, goal)
            if cached_plan:
                logger.info(f"使用缓存方案: {major} - {goal}")
                return cached_plan
        
        # 2. 从向量数据库检索相关信息（用于 RAG）
        # 注意：RAG 检索已在 generate_plan_with_llm 内部完成
        
        # 3. 调用大模型生成学习计划
        logger.info(f"调用大模型生成方案: {major} - {goal_zh}")
        result = generate_plan_with_llm(major, goal_zh, job)
        plan_dict = result.dict()
        
        # 调试日志：输出返回的数据结构
        logger.info(f"大模型返回数据: skill_tree长度={len(plan_dict.get('skill_tree', []))}, resources长度={len(plan_dict.get('resources', []))}, job_market长度={len(plan_dict.get('job_market', []))}")
        
        # 验证数据有效性
        is_valid = True
        skill_tree = plan_dict.get("skill_tree", [])
        resources = plan_dict.get("resources", [])
        job_market = plan_dict.get("job_market", [])
        
        if not isinstance(skill_tree, list) or len(skill_tree) == 0:
            logger.warning(f"学习计划数据无效: skill_tree 为空或格式错误")
            is_valid = False
        
        # 存入内存缓存（无论是否有效都缓存，避免重复调用大模型）
        cache_plan(major, goal, plan_dict)
        
        # 只有数据有效时才存入向量数据库
        if is_valid:
            try:
                from vector_db import get_vector_db
                vector_db = get_vector_db()
                
                # 将学习计划转换为文本格式存储（带时间戳）
                current_time = datetime.now().isoformat()
                plan_text = f"[生成时间: {current_time}] {major}专业{goal_zh}方向学习计划："
                for skill in skill_tree:
                    plan_text += f"\n- {skill.get('label', '')}"
                for resource in resources:
                    plan_text += f"\n- 推荐资源: {resource.get('title', '')}"
                for job_item in job_market:
                    plan_text += f"\n- 热门岗位: {job_item.get('name', '')}, 薪资: {job_item.get('salary', '')}"
                
                vector_db.add_documents([plan_text])
                logger.info(f"学习计划已存入向量数据库: {major} - {goal_zh} (时间: {current_time})")
            except Exception as e:
                logger.warning(f"存入向量数据库失败: {e}")
        else:
            logger.warning(f"跳过存入向量数据库: 数据无效")
        
        return success(data=plan_dict)
    
    except Exception as e:
        logger.error(f"错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


 