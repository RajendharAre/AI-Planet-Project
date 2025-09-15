"""
Chat API endpoints for workflow interaction
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.orm_models import ChatSession, ChatMessage, User, Document
from app.models.schemas import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse, ChatResponse,
    ChatSessionListResponse, BaseResponse
)
from app.api.V1.auth import get_current_active_user
from app.services.gemini_service import gemini_service

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    
    session = ChatSession(
        id=uuid.uuid4(),
        title=session_data.title,
        context_documents=session_data.context_documents,
        system_prompt=session_data.system_prompt,
        user_id=current_user.id
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return ChatSessionResponse.model_validate(session)

@router.get("/sessions", response_model=ChatSessionListResponse)
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all chat sessions for current user"""
    
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    
    return ChatSessionListResponse(
        message="Chat sessions retrieved successfully",
        sessions=[ChatSessionResponse.model_validate(session) for session in sessions],
        total=len(sessions)
    )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific chat session"""
    
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return ChatSessionResponse.model_validate(session)

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a chat session"""
    
    # Verify session belongs to user
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    
    return [ChatMessageResponse.model_validate(msg) for msg in messages]

@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_chat_message(
    session_id: uuid.UUID,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get AI response"""
    
    # Verify session belongs to user
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    start_time = datetime.utcnow()
    
    try:
        # Save user message
        user_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role="user",
            content=message_data.content
        )
        db.add(user_message)
        
        # Get context documents if specified
        context_content = []
        if session.context_documents:
            doc_result = await db.execute(
                select(Document).where(
                    Document.id.in_(session.context_documents),
                    Document.owner_id == current_user.id
                )
            )
            documents = doc_result.scalars().all()
            context_content = [doc.content for doc in documents if doc.content]
        
        # Generate AI response
        if context_content:
            ai_response = await gemini_service.chat_with_context(
                message_data.content, 
                context_content
            )
        else:
            ai_response = await gemini_service.generate_text(message_data.content)
        
        end_time = datetime.utcnow()
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Save AI response
        ai_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role="assistant",
            content=ai_response,
            response_time_ms=response_time_ms,
            model_used="gemini-1.5-flash",
            context_used={"documents_count": len(context_content)} if context_content else None
        )
        db.add(ai_message)
        
        # Update session
        session.message_count += 2
        session.last_message_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(ai_message)
        
        return ChatResponse(
            message="Message sent successfully",
            data=ChatMessageResponse.model_validate(ai_message)
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: uuid.UUID,
    session_update: ChatSessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session"""
    
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Update session fields
    update_data = session_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    await db.commit()
    await db.refresh(session)
    
    return ChatSessionResponse.model_validate(session)

@router.delete("/sessions/{session_id}", response_model=BaseResponse)
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    await db.delete(session)
    await db.commit()
    
    return BaseResponse(message="Chat session deleted successfully")