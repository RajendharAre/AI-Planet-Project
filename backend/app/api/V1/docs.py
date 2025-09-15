"""
Document processing API endpoints with Gemini AI integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid
import os
import aiofiles
from pathlib import Path
import mimetypes
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.orm_models import Document, DocumentChunk, User
from app.models.schemas import (
    DocumentResponse, DocumentCreate, DocumentUpdate, DocumentListResponse,
    DocumentUploadResponse, DocumentAnalysisRequest, DocumentAnalysisResponse,
    BaseResponse, ErrorResponse
)
from app.api.V1.auth import get_current_active_user
from app.services.gemini_service import gemini_service
from app.services.embeddings_service import embedding_service
from app.utils.pdf_utils import extract_text_from_pdf_bytes

router = APIRouter()

# Allowed file types
ALLOWED_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

def get_file_type(filename: str) -> tuple[str, str]:
    """Get file extension and MIME type"""
    ext = Path(filename).suffix.lower()
    mime_type = ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')
    return ext[1:] if ext else 'unknown', mime_type

async def save_uploaded_file(file: UploadFile, user_id: uuid.UUID) -> str:
    """Save uploaded file to disk"""
    # Create user-specific upload directory
    user_upload_dir = Path(settings.UPLOAD_DIR) / str(user_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    safe_filename = f"{file_id}{file_ext}"
    file_path = user_upload_dir / safe_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return str(file_path)

async def extract_text_content(file_path: str, file_type: str) -> str:
    """Extract text content from file"""
    try:
        if file_type == 'pdf':
            # Read file as bytes for PDF processing
            async with aiofiles.open(file_path, 'rb') as f:
                file_bytes = await f.read()
            return extract_text_from_pdf_bytes(file_bytes)
        elif file_type in ['txt', 'md']:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        else:
            return "Text extraction not supported for this file type"
    except Exception as e:
        return f"Error extracting text: {str(e)}"

async def create_document_chunks(document_id: uuid.UUID, content: str, db: AsyncSession):
    """Create document chunks for embeddings"""
    chunk_size = 1000  # characters per chunk
    overlap = 200      # character overlap between chunks
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(content):
        end = min(start + chunk_size, len(content))
        chunk_content = content[start:end]
        
        # Create embedding for chunk
        try:
            embedding = await embedding_service.create_embedding(chunk_content)
        except Exception as e:
            print(f"Warning: Failed to create embedding for chunk {chunk_index}: {e}")
            embedding = None
        
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=document_id,
            content=chunk_content,
            chunk_index=chunk_index,
            start_char=start,
            end_char=end,
            embedding=embedding,
            embedding_model="gemini" if embedding else None
        )
        
        chunks.append(chunk)
        db.add(chunk)
        
        start = max(start + chunk_size - overlap, end)
        chunk_index += 1
    
    return chunks

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    extract_text: bool = Form(True),
    analyze_content: bool = Form(True),
    create_embeddings: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document"""
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Validate file type
    file_type, mime_type = get_file_type(file.filename)
    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {list(ALLOWED_EXTENSIONS.keys())}"
        )
    
    try:
        # Save file
        file_path = await save_uploaded_file(file, current_user.id)
        
        # Create document record
        document = Document(
            id=uuid.uuid4(),
            title=title or file.filename,
            filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            file_type=file_type,
            mime_type=mime_type,
            owner_id=current_user.id,
            processing_status="processing"
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Extract text if requested
        if extract_text:
            try:
                content = await extract_text_content(file_path, file_type)
                document.content = content
                document.extraction_status = "completed"
                
                # Create chunks and embeddings if requested
                if create_embeddings and content:
                    await create_document_chunks(document.id, content, db)
                    document.embedding_status = "completed"
                
            except Exception as e:
                document.extraction_status = "failed"
                print(f"Text extraction failed: {e}")
        
        # Analyze content if requested
        if analyze_content and document.content:
            try:
                analysis = await gemini_service.analyze_document(document.content)
                document.summary = analysis.get("summary")
                document.topics = analysis.get("topics")
                document.entities = analysis.get("entities")
                document.insights = analysis.get("insights")
                document.metadata = {"document_type": analysis.get("document_type")}
            except Exception as e:
                print(f"Document analysis failed: {e}")
        
        document.processing_status = "completed"
        document.processed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(document)
        
        return DocumentUploadResponse(
            message="Document uploaded and processed successfully",
            document=DocumentResponse.model_validate(document)
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@router.post("/upload-public", response_model=DocumentUploadResponse)
async def upload_document_public(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    extract_text: bool = Form(True),
    analyze_content: bool = Form(True),
    create_embeddings: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document (public endpoint for testing)"""
    
    # Get or create default user for public uploads
    result = await db.execute(select(User).where(User.username == "admin"))
    default_user = result.scalar_one_or_none()
    
    if not default_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user not found. Please ensure database is initialized."
        )
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Validate file type
    file_type, mime_type = get_file_type(file.filename)
    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {list(ALLOWED_EXTENSIONS.keys())}"
        )
    
    try:
        # Save file
        file_path = await save_uploaded_file(file, default_user.id)
        
        # Create document record
        document = Document(
            id=uuid.uuid4(),
            title=title or file.filename,
            filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            file_type=file_type,
            mime_type=mime_type,
            owner_id=default_user.id,
            processing_status="processing"
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Extract text if requested
        if extract_text:
            try:
                content = await extract_text_content(file_path, file_type)
                document.content = content
                document.extraction_status = "completed"
                
                # Create chunks and embeddings if requested
                if create_embeddings and content:
                    await create_document_chunks(document.id, content, db)
                    document.embedding_status = "completed"
                
            except Exception as e:
                document.extraction_status = "failed"
                print(f"Text extraction failed: {e}")
        
        # Analyze content if requested
        if analyze_content and document.content:
            try:
                analysis = await gemini_service.analyze_document(document.content)
                document.summary = analysis.get("summary")
                document.topics = analysis.get("topics")
                document.entities = analysis.get("entities")
                document.insights = analysis.get("insights")
                document.metadata = {"document_type": analysis.get("document_type")}
            except Exception as e:
                print(f"Document analysis failed: {e}")
        
        document.processing_status = "completed"
        document.processed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(document)
        
        return DocumentUploadResponse(
            message="Document uploaded and processed successfully",
            document=DocumentResponse.model_validate(document)
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@router.get("/public", response_model=DocumentListResponse)
async def get_documents_public(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get all documents (public endpoint for frontend)"""
    
    # Get documents from admin user
    admin_result = await db.execute(select(User).where(User.username == "admin"))
    admin_user = admin_result.scalar_one_or_none()
    
    if not admin_user:
        return DocumentListResponse(
            message="No documents available",
            documents=[],
            total=0,
            page=1,
            per_page=limit
        )
    
    query = select(Document).where(Document.owner_id == admin_user.id)
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.owner_id == admin_user.id)
    )
    total = count_result.scalar()
    
    # Get documents
    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        message="Documents retrieved successfully",
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/", response_model=DocumentListResponse)
async def get_documents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    """Get user's documents with optional search"""
    
    query = select(Document).where(Document.owner_id == current_user.id)
    
    if search:
        query = query.where(
            Document.title.ilike(f"%{search}%") |
            Document.content.ilike(f"%{search}%")
        )
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.owner_id == current_user.id)
    )
    total = count_result.scalar()
    
    # Get documents
    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        message="Documents retrieved successfully",
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document"""
    
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a document"""
    
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update document fields
    update_data = document_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    await db.commit()
    await db.refresh(document)
    
    return DocumentResponse.model_validate(document)

@router.delete("/{document_id}", response_model=BaseResponse)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document"""
    
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from disk
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        print(f"Warning: Failed to delete file from disk: {e}")
    
    # Delete from database (will cascade delete chunks)
    await db.delete(document)
    await db.commit()
    
    return BaseResponse(message="Document deleted successfully")

@router.post("/{document_id}/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    document_id: uuid.UUID,
    analysis_request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze document content with Gemini AI"""
    
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not document.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no content to analyze"
        )
    
    try:
        start_time = datetime.utcnow()
        analysis = await gemini_service.analyze_document(document.content)
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Update document with analysis results
        if analysis_request.generate_summary:
            document.summary = analysis.get("summary")
        if analysis_request.analyze_topics:
            document.topics = analysis.get("topics")
        if analysis_request.analyze_entities:
            document.entities = analysis.get("entities")
        if analysis_request.extract_insights:
            document.insights = analysis.get("insights")
        
        await db.commit()
        
        return DocumentAnalysisResponse(
            message="Document analysis completed successfully",
            analysis=analysis,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
