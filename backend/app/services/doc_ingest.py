from app.utils.pdf_utils import extract_text_from_pdf_bytes
from app.services.embeddings_service import create_embedding
from app.services.chroma_client import get_chroma_client, get_collection

def ingest_pdf_bytes(filename: str, file_bytes: bytes, metadata: dict = None):
    text = extract_text_from_pdf_bytes(file_bytes)
    # naive chunking - production: use better chunker with overlap
    CHUNK_SIZE = 1000
    chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    client = get_chroma_client()
    col = get_collection(client)
    docs = []
    metadatas = []
    embeddings = []
    ids = []
    for i, chunk in enumerate(chunks):
        ids.append(f"{filename}::{i}")
        docs.append(chunk)
        metadatas.append({"source": filename, "chunk": i, **(metadata or {})})
        embeddings.append(create_embedding(chunk))
    col.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)
    # PersistentClient automatically persists data, no need to call persist()
    return {"status": "ok", "chunks_indexed": len(chunks)}
