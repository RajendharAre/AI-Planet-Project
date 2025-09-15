"""
Search API endpoints for document similarity search
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
import time
import numpy as np

from app.core.database import get_db
from app.models.orm_models import Document, DocumentChunk, User
from app.models.schemas import (
    SearchRequest, SearchResponse, SearchResult, BaseResponse
)
from app.api.V1.auth import get_current_active_user
from app.services.embeddings_service import embedding_service

router = APIRouter()

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    try:
        # Convert to numpy arrays
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot_product / (norm_a * norm_b)
        return float(similarity)
    except Exception:
        return 0.0

@router.post("/", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search documents using semantic similarity"""
    
    start_time = time.time()
    
    try:
        # Generate embedding for search query
        query_embedding = await embedding_service.create_embedding(search_request.query)
        
        # Build query to get document chunks
        chunk_query = select(DocumentChunk, Document).join(
            Document, DocumentChunk.document_id == Document.id
        ).where(
            Document.owner_id == current_user.id,
            DocumentChunk.embedding.isnot(None)
        )
        
        # Filter by specific documents if requested
        if search_request.document_ids:
            chunk_query = chunk_query.where(Document.id.in_(search_request.document_ids))
        
        result = await db.execute(chunk_query)
        chunks_with_docs = result.all()
        
        # Calculate similarities
        search_results = []
        for chunk, document in chunks_with_docs:
            if chunk.embedding:
                similarity = calculate_cosine_similarity(query_embedding, chunk.embedding)
                
                # Only include results above a minimum threshold
                if similarity > 0.1:  # Adjust threshold as needed
                    search_result = SearchResult(
                        document_id=document.id,
                        document_title=document.title,
                        chunk_content=chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content,
                        similarity_score=similarity,
                        metadata={
                            "chunk_index": chunk.chunk_index,
                            "document_filename": document.filename,
                            "document_type": document.file_type
                        }
                    )
                    search_results.append(search_result)
        
        # Sort by similarity score (highest first)
        search_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit results
        search_results = search_results[:search_request.limit]
        
        end_time = time.time()
        search_time_ms = (end_time - start_time) * 1000
        
        return SearchResponse(
            message="Search completed successfully",
            results=search_results,
            query=search_request.query,
            total_results=len(search_results),
            search_time_ms=search_time_ms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/documents/{document_id}/similar", response_model=SearchResponse)
async def find_similar_documents(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(5, ge=1, le=20)
):
    """Find documents similar to a given document"""
    
    start_time = time.time()
    
    # Get the source document
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id
        )
    )
    source_document = doc_result.scalar_one_or_none()
    
    if not source_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not source_document.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source document has no content"
        )
    
    try:
        # Use document content as search query
        search_request = SearchRequest(
            query=source_document.content[:1000],  # Use first 1000 chars
            limit=limit + 1,  # +1 to exclude the source document
            include_content=True
        )
        
        # Perform search
        search_results = await search_documents(search_request, current_user, db)
        
        # Filter out the source document from results
        filtered_results = [
            result for result in search_results.results 
            if result.document_id != document_id
        ][:limit]
        
        end_time = time.time()
        search_time_ms = (end_time - start_time) * 1000
        
        return SearchResponse(
            message="Similar documents found successfully",
            results=filtered_results,
            query=f"Similar to: {source_document.title}",
            total_results=len(filtered_results),
            search_time_ms=search_time_ms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similar document search failed: {str(e)}"
        )

@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    q: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(5, ge=1, le=10)
):
    """Get search suggestions based on document titles and content"""
    
    # Simple text-based suggestions from document titles
    result = await db.execute(
        select(Document.title, Document.summary).where(
            Document.owner_id == current_user.id,
            (Document.title.ilike(f"%{q}%") | Document.summary.ilike(f"%{q}%"))
        ).limit(limit)
    )
    
    suggestions = []
    for title, summary in result:
        suggestions.append(title)
        if summary and q.lower() in summary.lower():
            # Extract relevant snippet from summary
            words = summary.split()
            for i, word in enumerate(words):
                if q.lower() in word.lower():
                    start = max(0, i - 3)
                    end = min(len(words), i + 4)
                    snippet = " ".join(words[start:end])
                    suggestions.append(snippet)
                    break
    
    return list(set(suggestions))[:limit]  # Remove duplicates and limit