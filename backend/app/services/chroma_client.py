# Import warning suppressor first
from app.utils.chromadb_suppressor import suppress_chromadb_warnings
suppress_chromadb_warnings()

import chromadb
from chromadb.config import Settings
from app.core.config import settings
import os
import logging
import warnings

# Completely disable ChromaDB telemetry and warnings
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_DISABLED"] = "True"
os.environ["CHROMA_SERVER_NOFILE"] = "1"

# Suppress all ChromaDB related warnings and logs
warnings.filterwarnings("ignore", module="chromadb")
logging.getLogger("chromadb").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry.posthog").setLevel(logging.CRITICAL)

def get_chroma_client():
    # Ensure the persist directory exists
    persist_dir = settings.CHROMA_PERSIST_DIR
    os.makedirs(persist_dir, exist_ok=True)
    
    # Create client with telemetry completely disabled
    try:
        # Try creating with Settings to disable telemetry
        client_settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
        return chromadb.PersistentClient(path=persist_dir, settings=client_settings)
    except Exception:
        # Fallback to simple client creation
        return chromadb.PersistentClient(path=persist_dir)

def get_collection(client, name="ai_planet_collection"):
    try:
        return client.get_collection(name)
    except ValueError:
        # Collection doesn't exist, create it
        return client.create_collection(name)
