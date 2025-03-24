from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.models import schemas
from app.services import qa_service, novel_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ask", response_model=schemas.AnswerResponse)
async def ask_question(
    question_data: schemas.QuestionRequest,
    db: Session = Depends(get_db)
):
    """向小说提问"""
    # 检查小说是否存在
    novel = novel_service.get_novel(db=db, novel_id=question_data.novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    try:
        # 调用问答服务
        result = await qa_service.answer_question(
            db=db, 
            novel_id=question_data.novel_id,
            question=question_data.question,
            use_rag=question_data.use_rag
        )
        return result
    except Exception as e:
        logger.error(f"问答失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")

@router.post("/extract-entities", response_model=schemas.EntityExtractionResponse)
async def extract_entities(
    data: schemas.EntityExtractionRequest,
    db: Session = Depends(get_db)
):
    """从文本片段中提取实体"""
    try:
        # 如果提供了小说ID，先检查小说是否存在
        if data.novel_id:
            novel = novel_service.get_novel(db=db, novel_id=data.novel_id)
            if not novel:
                raise HTTPException(status_code=404, detail="小说不存在")
        
        # 调用实体提取服务
        result = await qa_service.extract_entities(text=data.text)
        return result
    except Exception as e:
        logger.error(f"实体提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"实体提取失败: {str(e)}")

@router.post("/analyze-text", response_model=dict)
async def analyze_text(
    data: schemas.EntityExtractionRequest,
    db: Session = Depends(get_db)
):
    """分析文本片段"""
    try:
        # 如果提供了小说ID，先检查小说是否存在
        if data.novel_id:
            novel = novel_service.get_novel(db=db, novel_id=data.novel_id)
            if not novel:
                raise HTTPException(status_code=404, detail="小说不存在")
        
        # 调用文本分析服务
        result = await qa_service.analyze_text(text=data.text)
        return result
    except Exception as e:
        logger.error(f"文本分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文本分析失败: {str(e)}") 