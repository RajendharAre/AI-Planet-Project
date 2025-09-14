import google.generativeai as genai
from openai import OpenAI
from app.core.config import settings
import logging
import hashlib

# Initialize logger
logger = logging.getLogger(__name__)

# Configure Gemini
has_gemini_key = (
    settings.GEMINI_API_KEY and 
    settings.GEMINI_API_KEY != "your_gemini_api_key_here" and 
    len(settings.GEMINI_API_KEY) > 10
)

if has_gemini_key:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini API configured successfully")
    except Exception as e:
        logger.warning(f"Failed to configure Gemini API: {e}")
        has_gemini_key = False
else:
    logger.warning("No valid Gemini API key found.")

# Check if we have a valid OpenAI API key (fallback)
has_openai_key = (
    settings.OPENAI_API_KEY and 
    settings.OPENAI_API_KEY != "your_openai_api_key_here" and 
    len(settings.OPENAI_API_KEY) > 10
)

if has_openai_key:
    try:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI client: {e}")
        has_openai_key = False

def create_embedding(text: str):
    """Create embeddings using configured provider (Gemini preferred, OpenAI fallback, dummy as last resort)"""
    
    # Check if dummy is explicitly requested
    if settings.EMBEDDING_PROVIDER == "dummy":
        logger.info("🤖 Using dummy embeddings (configured)")
        return _create_dummy_embedding(text)
    
    # First try Gemini if configured as primary provider
    elif settings.EMBEDDING_PROVIDER == "gemini" and has_gemini_key:
        return create_gemini_embedding(text)
    
    # Fallback to OpenAI if available
    elif has_openai_key:
        return _create_openai_embedding_direct(text)
    
    # Last resort: dummy embeddings
    else:
        logger.info("Using dummy embeddings (no valid API keys)")
        return _create_dummy_embedding(text)

def create_gemini_embedding(text: str):
    """Create embeddings using Google Gemini API"""
    try:
        # Use Gemini's embedding model
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        embedding = result['embedding']
        
        # Gemini returns 768 dimensions, but we need 1536 to match existing collection
        # Pad with zeros to match OpenAI dimension
        if len(embedding) == 768:
            embedding.extend([0.0] * (1536 - 768))  # Pad to 1536 dimensions
        
        logger.info("✅ Gemini embedding created successfully (padded to 1536 dims)")
        return embedding
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            logger.warning(f"⚠️  Gemini API quota exceeded: {e}")
        else:
            logger.error(f"❌ Gemini embedding failed: {e}")
        
        # Fall back to OpenAI if available
        if has_openai_key:
            logger.info("🔄 Falling back to OpenAI")
            return _create_openai_embedding_direct(text)
        else:
            logger.info("🔄 Falling back to dummy embeddings")
            return _create_dummy_embedding(text)

# Keep OpenAI function for compatibility/fallback
def _create_openai_embedding_direct(text: str):
    """Create embeddings using OpenAI API (direct call)"""
    try:
        # Using OpenAI Embeddings
        resp = openai_client.embeddings.create(input=text, model="text-embedding-3-small")
        logger.info("✅ OpenAI embedding created successfully")
        return resp.data[0].embedding
    except Exception as e:
        logger.error(f"❌ OpenAI embedding failed: {e}")
        # Fall back to dummy embedding
        logger.info("🔄 Falling back to dummy embeddings")
        return _create_dummy_embedding(text)

def create_openai_embedding(text: str):
    """Create embeddings using OpenAI API (public interface)"""
    return _create_openai_embedding_direct(text)

def _create_dummy_embedding(text: str, dimension: int = 1536):  # Match OpenAI dimensions for compatibility
    """Create a dummy embedding based on text hash for testing purposes"""
    # Create a deterministic embedding based on text hash
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Convert hash to numbers and normalize to create embedding-like vector
    embedding = []
    for i in range(0, dimension, 8):  # Process 8 chars at a time
        chunk = text_hash[i % len(text_hash):(i % len(text_hash)) + 8]
        if len(chunk) < 8:
            chunk = chunk.ljust(8, '0')
        
        # Convert hex to float and normalize
        try:
            val = int(chunk, 16) / (16**8)  # Normalize to 0-1
            embedding.append((val - 0.5) * 2)  # Center around 0, range -1 to 1
        except ValueError:
            embedding.append(0.0)
    
    # Ensure we have exactly the right dimension
    while len(embedding) < dimension:
        embedding.append(0.0)
    
    return embedding[:dimension]

# Legacy function name for backward compatibility
def create_openai_embedding_legacy(text: str):
    """Legacy function - use create_embedding instead"""
    return create_embedding(text)
