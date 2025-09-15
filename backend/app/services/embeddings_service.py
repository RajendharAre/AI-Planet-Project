from app.services.gemini_service import gemini_service
from app.core.config import settings
import logging
import hashlib
from typing import List, Union

# Initialize logger
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        
    async def create_embedding(self, text: str) -> List[float]:
        """Create embeddings using configured provider"""
        try:
            if self.provider == "gemini":
                return await self._create_gemini_embedding(text)
            elif self.provider == "dummy":
                return self._create_dummy_embedding(text)
            else:
                # Default to Gemini
                return await self._create_gemini_embedding(text)
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            # Fallback to dummy embedding
            return self._create_dummy_embedding(text)
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts"""
        try:
            if self.provider == "gemini":
                return await gemini_service.generate_embeddings(texts)
            else:
                return [self._create_dummy_embedding(text) for text in texts]
        except Exception as e:
            logger.error(f"Batch embedding creation failed: {e}")
            return [self._create_dummy_embedding(text) for text in texts]
    
    async def _create_gemini_embedding(self, text: str) -> List[float]:
        """Create embedding using Gemini service"""
        try:
            embeddings = await gemini_service.generate_embeddings([text])
            return embeddings[0] if embeddings else self._create_dummy_embedding(text)
        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            return self._create_dummy_embedding(text)
    
    def _create_dummy_embedding(self, text: str, dimension: int = 1536) -> List[float]:
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

# Global instance
embedding_service = EmbeddingService()

# Legacy functions for backward compatibility
def create_embedding(text: str):
    """Legacy sync function - use embedding_service.create_embedding instead"""
    import asyncio
    return asyncio.run(embedding_service.create_embedding(text))

def create_gemini_embedding(text: str):
    """Legacy function - use embedding_service instead"""
    return create_embedding(text)
