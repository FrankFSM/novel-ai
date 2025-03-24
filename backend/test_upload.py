#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from pathlib import Path
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from contextlib import contextmanager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入应用
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from app.core.database import Base, get_db
from app.models.novel import Novel, Chapter

def get_test_client():
    """获取测试客户端"""
    return TestClient(app)

def setup_test_db():
    """设置测试数据库"""
    # 使用临时文件作为测试数据库
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_url = f"sqlite:///{temp_db.name}"
    
    # 创建引擎和表
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    # 创建会话
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, TestingSessionLocal, temp_db.name

@contextmanager
def override_get_db(session_local):
    """临时覆盖get_db依赖"""
    def override_get_db():
        try:
            db = session_local()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db)

def test_db_permissions(engine):
    """测试数据库权限"""
    try:
        # 测试写入
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)"))
            conn.execute(text("INSERT INTO test_table (id) VALUES (1)"))
            conn.commit()
        logger.info("数据库写入测试成功")
        return True
    except Exception as e:
        logger.error(f"数据库写入测试失败: {str(e)}")
        return False

def test_novel_upload(client: TestClient, db_session):
    """测试小说上传功能"""
    # 创建测试文件
    test_content = """第一章 初入门派
这是第一章的内容。主角初入门派，开始了修仙之路。
在这里，他将开启一段不平凡的旅程。

第二章 修炼
这是第二章的内容。主角开始修炼基础功法。
他逐渐掌握了一些基本的修炼技巧。

第三章 历练
这是第三章的内容。主角外出历练，遇到了第一个对手。
这次经历让他明白了自己的不足。"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        test_file_path = f.name
    
    try:
        # 测试文件上传
        with open(test_file_path, 'rb') as f:
            response = client.post(
                "/api/v1/novels/upload-file",
                files={"file": ("test.txt", f, "text/plain")},
                data={
                    "title": "测试小说",
                    "author": "测试作者",
                    "description": "这是一个测试小说"
                }
            )
        
        # 检查响应
        assert response.status_code == 200, f"上传失败: {response.text}"
        data = response.json()
        assert "novel_id" in data, "响应中没有novel_id"
        
        # 验证数据库记录
        novel = db_session.query(Novel).filter(Novel.title == "测试小说").first()
        assert novel is not None, "数据库中没有找到小说记录"
        assert novel.author == "测试作者", "作者信息不匹配"
        
        # 验证章节
        chapters = db_session.query(Chapter).filter(Chapter.novel_id == novel.id).order_by(Chapter.number).all()
        assert len(chapters) == 3, f"章节数量不正确，期望3章，实际{len(chapters)}章"
        assert chapters[0].title == "第一章 初入门派", f"第一章标题不正确: {chapters[0].title}"
        assert "修仙之路" in chapters[0].content, "第一章内容不正确"
        
        logger.info(f"小说上传测试成功，成功创建{len(chapters)}个章节")
        return True
    
    except Exception as e:
        logger.error(f"小说上传测试失败: {str(e)}")
        return False
    
    finally:
        # 清理测试文件
        os.unlink(test_file_path)

def main():
    """主测试流程"""
    # 设置测试数据库
    engine, TestingSessionLocal, db_path = setup_test_db()
    
    try:
        # 测试数据库权限
        if not test_db_permissions(engine):
            logger.error("数据库权限测试失败")
            return False
        
        # 覆盖数据库依赖
        with override_get_db(TestingSessionLocal):
            # 创建测试客户端
            client = get_test_client()
            
            # 获取数据库会话
            db = TestingSessionLocal()
            
            try:
                # 测试小说上传
                if not test_novel_upload(client, db):
                    logger.error("小说上传测试失败")
                    return False
                
                logger.info("所有测试通过")
                return True
            finally:
                db.close()
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}")
        return False
        
    finally:
        # 清理测试数据库
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 