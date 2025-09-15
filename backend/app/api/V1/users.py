"""
User management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.models.orm_models import User, Document, Workflow, ChatSession
from app.models.schemas import (
    UserResponse, UserUpdate, BaseResponse, UserStatsResponse,
    ErrorResponse
)
from app.api.V1.auth import get_current_active_user, get_password_hash

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    
    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        result = await db.execute(select(User).where(User.email == user_update.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics"""
    
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
    
    # Calculate storage used (sum of file sizes)
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

@router.delete("/account", response_model=BaseResponse)
async def delete_user_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user account and all associated data"""
    
    # This will cascade delete all related documents, workflows, etc.
    await db.delete(current_user)
    await db.commit()
    
    return BaseResponse(message="Account deleted successfully")

@router.post("/deactivate", response_model=BaseResponse)
async def deactivate_user_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate current user account"""
    
    current_user.is_active = False
    await db.commit()
    
    return BaseResponse(message="Account deactivated successfully")

# Admin-only endpoints
@router.get("/all", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all users (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    
    return [UserResponse.model_validate(user) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@router.put("/{user_id}/admin", response_model=BaseResponse)
async def toggle_admin_status(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle admin status for a user (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_admin = not user.is_admin
    await db.commit()
    
    status_text = "granted" if user.is_admin else "revoked"
    return BaseResponse(message=f"Admin privileges {status_text} for user {user.username}")