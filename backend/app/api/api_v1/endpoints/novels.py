from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.core.database import get_db
from app.models import schemas, novel
from app.services import novel_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.NovelResponse)
async def create_novel(
    novel_data: schemas.NovelCreate,
    db: Session = Depends(get_db)
):
    """创建新小说"""
    return novel_service.create_novel(db=db, novel_data=novel_data)

@router.get("/", response_model=List[schemas.NovelResponse])
async def get_novels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取所有小说"""
    return novel_service.get_novels(db=db, skip=skip, limit=limit)

@router.get("/{novel_id}", response_model=schemas.NovelDetail)
async def get_novel(
    novel_id: int,
    db: Session = Depends(get_db)
):
    """获取小说详情"""
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 创建NovelDetail对象，包含所需的计数字段
    novel_detail = schemas.NovelDetail(
        id=db_novel.id,
        title=db_novel.title,
        author=db_novel.author,
        description=db_novel.description,
        cover_url=db_novel.cover_url,
        created_at=db_novel.created_at,
        updated_at=db_novel.updated_at,
        chapters_count=len(db_novel.chapters) if hasattr(db_novel, "chapters") else 0,
        characters_count=len(db_novel.characters) if hasattr(db_novel, "characters") else 0
    )
    return novel_detail

@router.put("/{novel_id}", response_model=schemas.NovelResponse)
async def update_novel(
    novel_id: int,
    novel_data: schemas.NovelCreate,
    db: Session = Depends(get_db)
):
    """更新小说信息"""
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="小说不存在")
    return novel_service.update_novel(db=db, novel_id=novel_id, novel_data=novel_data)

@router.delete("/{novel_id}")
async def delete_novel(
    novel_id: int,
    db: Session = Depends(get_db)
):
    """删除小说"""
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="小说不存在")
    novel_service.delete_novel(db=db, novel_id=novel_id)
    return {"message": "小说删除成功"}

@router.post("/upload-file", response_model=schemas.UploadNovelResponse)
async def upload_novel_file(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    author: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传小说文件"""
    try:
        # 先创建小说记录
        novel_data = schemas.NovelCreate(
            title=title,
            author=author,
            description=description
        )
        db_novel = novel_service.create_novel(db=db, novel_data=novel_data)
        
        # 读取文件内容
        content = await file.read()
        text = content.decode('utf-8')
        
        # 直接处理文件内容
        await novel_service.process_novel_content(db=db, novel_id=db_novel.id, content=text)
        
        return {
            "novel_id": db_novel.id,
            "message": "小说文件上传成功"
        }
    except Exception as e:
        logger.error(f"小说文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"小说文件上传失败: {str(e)}")

@router.get("/{novel_id}/statistics", response_model=Dict[str, Any])
async def get_novel_statistics(
    novel_id: int,
    db: Session = Depends(get_db)
):
    """获取小说统计信息"""
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    return novel_service.get_novel_statistics(db=db, novel_id=novel_id)

@router.post("/{novel_id}/extract-entities", response_model=schemas.EntityExtractionResponse)
async def extract_novel_entities(
    novel_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """提取小说实体（异步任务）"""
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 启动后台任务提取实体
    background_tasks.add_task(
        novel_service.extract_novel_entities,
        db=db,
        novel_id=novel_id
    )
    
    return {
        "message": "实体提取任务已启动，将在后台处理"
    } 