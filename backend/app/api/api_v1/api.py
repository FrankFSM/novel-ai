from fastapi import APIRouter

from app.api.api_v1.endpoints import novels, chapters, characters, analysis, qa

api_router = APIRouter()

# 添加各模块路由
api_router.include_router(novels.router, prefix="/novels", tags=["novels"])
api_router.include_router(chapters.router, prefix="/chapters", tags=["chapters"])
api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"]) 