from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Novel(Base):
    """小说模型"""
    __tablename__ = "novels"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    chapters = relationship("Chapter", back_populates="novel", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="novel", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="novel", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="novel", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="novel", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="novel", cascade="all, delete-orphan")
    relationship_graphs = relationship("RelationshipGraph", back_populates="novel", cascade="all, delete-orphan")

class Chapter(Base):
    """章节模型"""
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    number = Column(Integer, nullable=False)  # 章节序号
    word_count = Column(Integer, nullable=True)  # 字数统计
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    novel = relationship("Novel", back_populates="chapters")
    chunks = relationship("TextChunk", back_populates="chapter", cascade="all, delete-orphan")

class TextChunk(Base):
    """文本块模型（用于向量检索）"""
    __tablename__ = "text_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    content = Column(Text, nullable=False)
    start_char = Column(Integer, nullable=False)  # 在章节中的起始位置
    end_char = Column(Integer, nullable=False)    # 在章节中的结束位置
    vector_id = Column(String(50), nullable=True)  # 在向量数据库中的ID
    
    # 关系
    chapter = relationship("Chapter", back_populates="chunks")
    entities = relationship("EntityMention", back_populates="chunk")

class Character(Base):
    """角色模型"""
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    alias = Column(JSON, nullable=True)  # 别名列表
    description = Column(Text, nullable=True)
    first_appearance = Column(Integer, ForeignKey("chapters.id"), nullable=True)  # 首次出场章节
    
    # 关系
    novel = relationship("Novel", back_populates="characters")
    mentions = relationship("EntityMention", back_populates="character")
    from_relationships = relationship("Relationship", foreign_keys="Relationship.from_character_id", back_populates="from_character")
    to_relationships = relationship("Relationship", foreign_keys="Relationship.to_character_id", back_populates="to_character")
    owned_items = relationship("Item", back_populates="owner")
    participations = relationship("EventParticipation", back_populates="character")
    relationship_graphs = relationship("RelationshipGraph", back_populates="character", cascade="all, delete-orphan")

class Location(Base):
    """地点模型"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # 父级地点（如华山属于五岳）
    
    # 关系
    novel = relationship("Novel", back_populates="locations")
    mentions = relationship("EntityMention", back_populates="location")
    children = relationship("Location", back_populates="parent")
    parent = relationship("Location", back_populates="children", remote_side=[id])
    events = relationship("Event", back_populates="location")

class Item(Base):
    """物品模型"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("characters.id"), nullable=True)  # 当前拥有者
    
    # 关系
    novel = relationship("Novel", back_populates="items")
    mentions = relationship("EntityMention", back_populates="item")
    owner = relationship("Character", back_populates="owned_items")
    transfers = relationship("ItemTransfer", back_populates="item")

class Event(Base):
    """事件模型"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)  # 发生章节
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # 发生地点
    time_description = Column(String(255), nullable=True)  # 时间描述
    importance = Column(Integer, default=1)  # 重要性评分（1-5）
    
    # 关系
    novel = relationship("Novel", back_populates="events")
    mentions = relationship("EntityMention", back_populates="event")
    location = relationship("Location", back_populates="events")
    participants = relationship("EventParticipation", back_populates="event")
    
class Relationship(Base):
    """人物关系模型"""
    __tablename__ = "relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    from_character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    to_character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)  # 关系类型：师徒、情侣、仇敌等
    description = Column(Text, nullable=True)
    first_chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)  # 关系建立章节
    
    # 关系
    novel = relationship("Novel", back_populates="relationships")
    from_character = relationship("Character", foreign_keys=[from_character_id], back_populates="from_relationships")
    to_character = relationship("Character", foreign_keys=[to_character_id], back_populates="to_relationships")

class EntityMention(Base):
    """实体提及模型（记录实体在文本中的出现）"""
    __tablename__ = "entity_mentions"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("text_chunks.id"), nullable=False)
    start_char = Column(Integer, nullable=False)  # 在文本块中的起始位置
    end_char = Column(Integer, nullable=False)    # 在文本块中的结束位置
    
    # 实体类型（只设置一个不为空）
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    
    # 关系
    chunk = relationship("TextChunk", back_populates="entities")
    character = relationship("Character", back_populates="mentions")
    location = relationship("Location", back_populates="mentions")
    item = relationship("Item", back_populates="mentions")
    event = relationship("Event", back_populates="mentions")

class EventParticipation(Base):
    """事件参与模型（记录角色参与事件的关系）"""
    __tablename__ = "event_participations"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    role = Column(String(50), nullable=True)  # 在事件中的角色：主导者、受害者等
    
    # 关系
    event = relationship("Event", back_populates="participants")
    character = relationship("Character", back_populates="participations")

class ItemTransfer(Base):
    """物品转移记录（物品易主记录）"""
    __tablename__ = "item_transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    from_character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    to_character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)  # 发生章节
    description = Column(Text, nullable=True)
    
    # 关系
    item = relationship("Item", back_populates="transfers")
    from_character = relationship("Character", foreign_keys=[from_character_id])
    to_character = relationship("Character", foreign_keys=[to_character_id])

class RelationshipGraph(Base):
    """关系网络分析结果表"""
    __tablename__ = "relationship_graphs"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=True)
    depth = Column(Integer, default=1)
    
    # 存储节点数据
    nodes = Column(JSON)
    
    # 创建和更新时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 设置外键关系
    novel = relationship("Novel", back_populates="relationship_graphs")
    character = relationship("Character", back_populates="relationship_graphs")
    edges = relationship("RelationshipEdge", back_populates="graph", cascade="all, delete-orphan")

class RelationshipEdge(Base):
    """关系网络边数据表"""
    __tablename__ = "relationship_edges"
    
    id = Column(Integer, primary_key=True, index=True)
    graph_id = Column(Integer, ForeignKey("relationship_graphs.id", ondelete="CASCADE"), nullable=False)
    
    source_id = Column(Integer, nullable=False)
    target_id = Column(Integer, nullable=False)
    source_name = Column(String, nullable=False)
    target_name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    importance = Column(Float, default=1.0)
    
    # 关联到图表
    graph = relationship("RelationshipGraph", back_populates="edges") 