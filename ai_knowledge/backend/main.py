"""AI 知识图谱后端服务 - 主入口"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from database import engine, Base
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from utils.limiter import limiter
from utils.logger import setup_logger

# 初始化日志系统
logger = setup_logger()

# 加载环境变量
load_dotenv()

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 实例
app = FastAPI(title="AI 知识图谱", description="学业领航员后端服务")

# 注册速率限制
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("AI 知识图谱后端服务已启动")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 导入并注册路由
from api.auth import router as auth_router
from api.user import router as user_router
from api.plan import router as plan_router
from api.forum import router as forum_router
from api.life import router as life_router
from api.admin import router as admin_router

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(plan_router)
app.include_router(forum_router)
app.include_router(life_router)
app.include_router(admin_router)


# --- 自定义中文速率限制提示 ---
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "请求过于频繁，请稍后再试"},
        headers={"Retry-After": str(exc.retry_after)},
    )


# ============ 主程序入口 ============

if __name__ == "__main__":
    import uvicorn

    logger.info("AI 知识图谱后端服务启动中...")
    uvicorn.run(app, host="127.0.0.1", port=8000)