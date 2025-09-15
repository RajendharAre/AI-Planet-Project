"""
Gemini AI Service for document processing, embeddings, and chat functionality
"""
# Fixed dependencies
import google.generativeai as genai
import asyncio
import aiohttp
import numpy as np
from typing import List, Optional, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
            logger.warning("Gemini API key not configured - AI responses will be limited")
            self._api_configured = False
            return
        
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Initialize models
            self.text_model = genai.GenerativeModel('gemini-1.5-flash')
            self.embedding_model = 'models/text-embedding-004'
            self._api_configured = True
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            self._api_configured = False
        
        # Configure generation settings for faster response
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 1024,  # Reduced for faster response
        }
        
        # Configure safety settings
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]

    async def generate_text(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate text using Gemini AI
        """
        if not self._api_configured:
            return "AI service is not configured. Please add your Gemini API key to the backend .env file to enable AI responses."
        
        try:
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.text_model.generate_content(
                    full_prompt,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
            )
            
            if response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini API")
                return "I apologize, but I couldn't generate a response to your question."
                
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            return f"AI service error: {str(e)}. Please check the API configuration."

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Gemini
        Note: Gemini embeddings are 768-dimensional, we'll pad to 1536 for compatibility
        """
        try:
            embeddings = []
            
            for text in texts:
                # Generate embedding using Gemini
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: genai.embed_content(
                        model=self.embedding_model,
                        content=text,
                        task_type="retrieval_document"
                    )
                )
                
                embedding = result['embedding']
                
                # Pad embedding from 768 to 1536 dimensions for compatibility
                if len(embedding) == 768:
                    # Pad with zeros to reach 1536 dimensions
                    padded_embedding = embedding + [0.0] * (1536 - 768)
                    embeddings.append(padded_embedding)
                else:
                    embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings with Gemini: {e}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")

    async def analyze_document(self, text: str) -> Dict[str, Any]:
        """
        Analyze document content and extract key information
        """
        try:
            analysis_prompt = f"""
            Analyze the following document and provide a comprehensive analysis:
            
            Document:
            {text}
            
            Please provide:
            1. Summary (2-3 sentences)
            2. Key topics/themes
            3. Main entities (people, organizations, locations)
            4. Document type/category
            5. Key insights or findings
            
            Format your response as JSON with the following structure:
            {{
                "summary": "Brief summary here",
                "topics": ["topic1", "topic2", "topic3"],
                "entities": {{
                    "people": ["person1", "person2"],
                    "organizations": ["org1", "org2"],
                    "locations": ["location1", "location2"]
                }},
                "document_type": "type here",
                "insights": ["insight1", "insight2"]
            }}
            """
            
            response = await self.generate_text(analysis_prompt)
            
            # Try to parse as JSON, fallback to plain text if needed
            try:
                import json
                analysis = json.loads(response)
            except:
                analysis = {
                    "summary": response[:200] + "...",
                    "topics": ["General Content"],
                    "entities": {"people": [], "organizations": [], "locations": []},
                    "document_type": "Unknown",
                    "insights": ["Analysis available in summary"]
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing document with Gemini: {e}")
            raise Exception(f"Failed to analyze document: {str(e)}")

    async def chat_with_context(self, question: str, context_documents: List[str]) -> str:
        """
        Answer questions based on provided document context
        """
        if not self._api_configured:
            return "AI service is not configured. Please add your Gemini API key to the backend .env file to enable AI responses with document context."
        
        try:
            # Combine context documents
            combined_context = "\n\n".join(context_documents)
            
            chat_prompt = f"""
            You are an AI assistant helping users understand and analyze documents. 
            Use the provided context to answer the user's question accurately and helpfully.
            
            Context Documents:
            {combined_context}
            
            User Question: {question}
            
            Please provide a comprehensive answer based on the context. If the answer isn't 
            directly available in the context, let the user know and provide the best 
            possible guidance based on the available information.
            """
            
            response = await self.generate_text(chat_prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error in chat with context: {e}")
            return f"AI service error in context chat: {str(e)}"

    async def summarize_conversation(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Summarize a conversation history
        """
        try:
            # Format conversation history
            formatted_history = ""
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                formatted_history += f"{role.title()}: {content}\n"
            
            summary_prompt = f"""
            Please provide a concise summary of the following conversation:
            
            {formatted_history}
            
            Summary should include:
            - Main topics discussed
            - Key questions asked
            - Important answers or insights provided
            - Current context of the conversation
            """
            
            response = await self.generate_text(summary_prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            raise Exception(f"Failed to summarize conversation: {str(e)}")

    async def health_check(self) -> bool:
        """
        Check if Gemini API is accessible and working
        """
        try:
            test_response = await self.generate_text("Hello, this is a health check.")
            return len(test_response) > 0
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False

    async def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using SerpAPI (if available) or fallback to Gemini knowledge
        """
        try:
            if hasattr(settings, 'SERP_API_KEY') and settings.SERP_API_KEY:
                # Use SerpAPI for web search
                return await self._search_with_serp(query, num_results)
            else:
                # Fallback to Gemini knowledge
                search_prompt = f"""
                Based on your training data, provide information about: {query}
                
                Please provide a comprehensive response with:
                1. Key facts and information
                2. Recent developments (if known)
                3. Related topics or concepts
                4. Reliable sources or references (if available)
                
                Format your response in a structured way.
                """
                
                response = await self.generate_text(search_prompt)
                return [{
                    "title": "AI Knowledge Response",
                    "snippet": response[:500] + "..." if len(response) > 500 else response,
                    "url": "ai-generated",
                    "source": "Gemini AI"
                }]
                
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return []

    async def _search_with_serp(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """
        Search using SerpAPI
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'q': query,
                    'api_key': settings.SERP_API_KEY,
                    'num': num_results,
                    'engine': 'google'
                }
                
                async with session.get('https://serpapi.com/search', params=params) as response:
                    data = await response.json()
                    
                    results = []
                    for result in data.get('organic_results', [])[:num_results]:
                        results.append({
                            'title': result.get('title', ''),
                            'snippet': result.get('snippet', ''),
                            'url': result.get('link', ''),
                            'source': 'web'
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []

# Create global instance
gemini_service = GeminiService()