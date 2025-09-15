"""
Analytics API endpoints for system statistics and insights
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.orm_models import User, Document, Workflow, ChatSession, ChatMessage
from app.models.schemas import (
    UserStatsResponse, SystemStatsResponse, BaseResponse
)
from app.api.V1.auth import get_current_active_user

router = APIRouter()

@router.get("/user/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive user statistics"""
    
    # Count documents
    doc_result = await db.execute(
        select(func.count(Document.id)).where(Document.owner_id == current_user.id)
    )
    total_documents = doc_result.scalar()
    
    # Count workflows
    wf_result = await db.execute(
        select(func.count(Workflow.id)).where(Workflow.owner_id == current_user.id)
    )
    total_workflows = wf_result.scalar()
    
    # Count chat sessions
    chat_result = await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == current_user.id)
    )
    total_chat_sessions = chat_result.scalar()
    
    # Calculate storage used
    storage_result = await db.execute(
        select(func.coalesce(func.sum(Document.file_size), 0)).where(Document.owner_id == current_user.id)
    )
    storage_used_bytes = storage_result.scalar()
    
    return UserStatsResponse(
        total_documents=total_documents,
        total_workflows=total_workflows,
        total_chat_sessions=total_chat_sessions,
        storage_used_bytes=storage_used_bytes,
        last_activity=current_user.last_login
    )

@router.get("/user/activity", response_model=Dict[str, Any])
async def get_user_activity(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    days: int = 30
):
    """Get user activity over the past N days"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Documents uploaded over time
    doc_activity = await db.execute(
        select(
            func.date(Document.created_at).label('date'),
            func.count(Document.id).label('count')
        ).where(
            Document.owner_id == current_user.id,
            Document.created_at >= start_date
        ).group_by(func.date(Document.created_at))
        .order_by(func.date(Document.created_at))
    )
    
    # Chat messages over time
    chat_activity = await db.execute(
        select(
            func.date(ChatMessage.created_at).label('date'),
            func.count(ChatMessage.id).label('count')
        ).join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(
            ChatSession.user_id == current_user.id,
            ChatMessage.created_at >= start_date
        ).group_by(func.date(ChatMessage.created_at))
        .order_by(func.date(ChatMessage.created_at))
    )
    
    return {
        "document_uploads": [
            {"date": str(row.date), "count": row.count} 
            for row in doc_activity
        ],
        "chat_messages": [
            {"date": str(row.date), "count": row.count} 
            for row in chat_activity
        ]
    }

@router.get("/user/documents/insights", response_model=Dict[str, Any])
async def get_document_insights(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get insights about user's documents"""
    
    # File type distribution
    file_types = await db.execute(
        select(
            Document.file_type,
            func.count(Document.id).label('count'),
            func.sum(Document.file_size).label('total_size')
        ).where(Document.owner_id == current_user.id)
        .group_by(Document.file_type)
    )
    
    # Processing status distribution
    processing_status = await db.execute(
        select(
            Document.processing_status,
            func.count(Document.id).label('count')
        ).where(Document.owner_id == current_user.id)
        .group_by(Document.processing_status)
    )
    
    # Most recent documents
    recent_docs = await db.execute(
        select(Document.title, Document.created_at, Document.file_type)
        .where(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
        .limit(5)
    )
    
    return {
        "file_types": [
            {
                "type": row.file_type,
                "count": row.count,
                "total_size": row.total_size or 0
            } for row in file_types
        ],
        "processing_status": [
            {"status": row.processing_status, "count": row.count}
            for row in processing_status
        ],
        "recent_documents": [
            {
                "title": doc.title,
                "created_at": doc.created_at.isoformat(),
                "file_type": doc.file_type
            } for doc in recent_docs
        ]
    }

@router.get("/system/stats", response_model=SystemStatsResponse)
async def get_system_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system-wide statistics (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Count total users
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar()
    
    # Count total documents
    docs_result = await db.execute(select(func.count(Document.id)))
    total_documents = docs_result.scalar()
    
    # Count total workflows
    wf_result = await db.execute(select(func.count(Workflow.id)))
    total_workflows = wf_result.scalar()
    
    # Count total chat sessions
    chat_result = await db.execute(select(func.count(ChatSession.id)))
    total_chat_sessions = chat_result.scalar()
    
    # Active sessions (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    active_result = await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.last_message_at >= yesterday)
    )
    active_sessions = active_result.scalar()
    
    # Messages today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_messages = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.created_at >= today)
    )
    api_calls_today = today_messages.scalar()
    
    return SystemStatsResponse(
        total_users=total_users,
        total_documents=total_documents,
        total_workflows=total_workflows,
        total_chat_sessions=total_chat_sessions,
        api_calls_today=api_calls_today,
        active_sessions=active_sessions
    )

@router.get("/system/health", response_model=Dict[str, Any])
async def get_system_health(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system health status"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Test database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Check Gemini API status
    from app.services.gemini_service import gemini_service
    try:
        gemini_status = "healthy" if await gemini_service.health_check() else "unhealthy"
    except Exception:
        gemini_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" and gemini_status == "healthy" else "degraded",
        "services": {
            "database": db_status,
            "gemini_api": gemini_status,
            "api": "healthy"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/reports/usage", response_model=Dict[str, Any])
async def get_usage_report(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    days: int = 7
):
    """Get usage report for the past N days"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily user registrations
    registrations = await db.execute(
        select(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).where(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    
    # Daily document uploads
    uploads = await db.execute(
        select(
            func.date(Document.created_at).label('date'),
            func.count(Document.id).label('count'),
            func.sum(Document.file_size).label('total_size')
        ).where(Document.created_at >= start_date)
        .group_by(func.date(Document.created_at))
        .order_by(func.date(Document.created_at))
    )
    
    # Daily chat activity
    chat_activity = await db.execute(
        select(
            func.date(ChatMessage.created_at).label('date'),
            func.count(ChatMessage.id).label('count')
        ).where(ChatMessage.created_at >= start_date)
        .group_by(func.date(ChatMessage.created_at))
        .order_by(func.date(ChatMessage.created_at))
    )
    
    return {
        "period_days": days,
        "user_registrations": [
            {"date": str(row.date), "count": row.count}
            for row in registrations
        ],
        "document_uploads": [
            {
                "date": str(row.date),
                "count": row.count,
                "total_size": row.total_size or 0
            } for row in uploads
        ],
        "chat_activity": [
            {"date": str(row.date), "count": row.count}
            for row in chat_activity
        ]
    }