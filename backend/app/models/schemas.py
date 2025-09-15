"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import uuid

# Base Models
class BaseResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# User Models
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_admin: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

# Document Models
class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    file_type: str
    mime_type: str

class DocumentCreate(DocumentBase):
    filename: str
    file_size: int
    content: Optional[str] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    file_path: str
    file_size: int
    processing_status: str
    extraction_status: str
    embedding_status: str
    summary: Optional[str] = None
    topics: Optional[List[str]] = None
    entities: Optional[Dict[str, List[str]]] = None
    insights: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    owner_id: UUID

class DocumentUploadResponse(BaseResponse):
    document: DocumentResponse

class DocumentListResponse(BaseResponse):
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int

# Document Analysis Models
class DocumentAnalysisRequest(BaseModel):
    analyze_entities: bool = True
    analyze_topics: bool = True
    generate_summary: bool = True
    extract_insights: bool = True

class DocumentAnalysisResponse(BaseResponse):
    analysis: Dict[str, Any]
    processing_time: float

# Workflow Models
class WorkflowNodeCreate(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]

class WorkflowEdgeCreate(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class WorkflowCreate(WorkflowBase):
    nodes: List[WorkflowNodeCreate] = []
    edges: List[WorkflowEdgeCreate] = []
    config: Optional[Dict[str, Any]] = None

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNodeCreate]] = None
    edges: Optional[List[WorkflowEdgeCreate]] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class WorkflowResponse(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    status: str
    execution_count: int
    last_executed: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: UUID

class WorkflowListResponse(BaseResponse):
    workflows: List[WorkflowResponse]
    total: int

class WorkflowExecutionRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = None
    document_ids: Optional[List[UUID]] = None

class WorkflowExecutionResponse(BaseResponse):
    execution_id: UUID
    status: str
    output_data: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[float] = None
    tokens_used: Optional[int] = None

# Chat Models
class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"
    context_documents: Optional[List[UUID]] = None
    system_prompt: Optional[str] = None

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    context_documents: Optional[List[UUID]] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None

class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    context_documents: Optional[List[UUID]] = None
    system_prompt: Optional[str] = None
    is_active: bool
    message_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    user_id: UUID

class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    role: str = Field(default="user", pattern="^(user|assistant|system)$")

class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    role: str
    content: str
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    context_used: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    session_id: UUID

class ChatResponse(BaseResponse):
    message: ChatMessageResponse
    conversation_context: Optional[List[ChatMessageResponse]] = None

class ChatSessionListResponse(BaseResponse):
    sessions: List[ChatSessionResponse]
    total: int

# Search Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_ids: Optional[List[UUID]] = None
    limit: int = Field(default=10, ge=1, le=50)
    include_content: bool = True

class SearchResult(BaseModel):
    document_id: UUID
    document_title: str
    chunk_content: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseResponse):
    results: List[SearchResult]
    query: str
    total_results: int
    search_time_ms: float

# File Upload Models
class FileUploadRequest(BaseModel):
    extract_text: bool = True
    analyze_content: bool = True
    create_embeddings: bool = True

# System Models
class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str]
    uptime_seconds: float

class SystemSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    key: str
    value: Any
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# Statistics Models
class UserStatsResponse(BaseModel):
    total_documents: int
    total_workflows: int
    total_chat_sessions: int
    storage_used_bytes: int
    last_activity: Optional[datetime] = None

class SystemStatsResponse(BaseModel):
    total_users: int
    total_documents: int
    total_workflows: int
    total_chat_sessions: int
    api_calls_today: int
    active_sessions: int