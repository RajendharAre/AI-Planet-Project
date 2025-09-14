from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from .dp import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    definition = Column(JSON, nullable=False)  # nodes + edges
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatLog(Base):
    __tablename__ = "chat_logs"
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, nullable=True)
    user_query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
