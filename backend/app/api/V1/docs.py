from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.doc_ingest import ingest_pdf_bytes
from app.models.orm_models import Document
from app.models.dp import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

router = APIRouter(prefix="/docs", tags=["docs"])

@router.post("/upload")
async def upload_doc(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDFs supported for now")
    contents = await file.read()
    ingest_result = ingest_pdf_bytes(file.filename, contents)
    # Save metadata
    stmt = insert(Document).values(filename=file.filename, content="(content omitted for DB)", doc_metadata={"ingest": ingest_result})
    await db.execute(stmt)
    await db.commit()
    return {"status": "ok", **ingest_result}
