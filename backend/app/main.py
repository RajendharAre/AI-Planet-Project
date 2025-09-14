# Import ChromaDB warning suppressor FIRST
from app.utils.chromadb_suppressor import suppress_chromadb_warnings
suppress_chromadb_warnings()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.V1.docs import router as docs_router
from app.api.V1.workflows import router as wf_router
import os
import warnings

# Additional telemetry suppression
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_DISABLED"] = "True"
warnings.filterwarnings("ignore", message=".*telemetry.*")
warnings.filterwarnings("ignore", message=".*capture.*")

app = FastAPI(title="AI Planet - Workflow Engine")

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:5174",  # Vite alternative port
        "http://localhost:3000",  # React default port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs_router)
app.include_router(wf_router)

@app.get("/")
async def root():
    return {"status":"ok", "service":"ai-planet-workflows"}
