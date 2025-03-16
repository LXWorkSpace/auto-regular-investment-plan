import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.api.routes import router

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="自动定投策略提醒系统",
    description="基于估值择时、趋势跟踪和波动率适配的智能定投策略提醒系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(router, prefix="/api")

# 根路由
@app.get("/")
async def root():
    return {"message": "自动定投策略提醒系统API"}

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 启动服务器
if __name__ == "__main__":
    # 获取运行端口
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 