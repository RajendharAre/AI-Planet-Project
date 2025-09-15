"""
Advanced Workflow Engine for No-Code/Low-Code workflow execution
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from app.services.gemini_service import gemini_service
from app.services.embeddings_service import embedding_service
from app.models.orm_models import Document, DocumentChunk, User
from app.core.config import settings

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    Advanced workflow engine that executes user-defined workflows
    with the 4 core components: UserQuery, KnowledgeBase, LLMEngine, Output
    """
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.execution_context = {}
        
    async def execute_workflow(
        self, 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow defined by nodes and edges
        """
        try:
            # Build execution graph
            execution_graph = self._build_execution_graph(nodes, edges)
            
            # Find starting node (UserQuery)
            start_node = self._find_start_node(nodes)
            if not start_node:
                raise Exception("No UserQuery component found")
            
            # Execute workflow step by step
            result = await self._execute_node_sequence(execution_graph, start_node, input_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise e
    
    def _build_execution_graph(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """
        Build an execution graph from nodes and edges
        """
        graph = {}
        
        # Initialize nodes in graph
        for node in nodes:
            node_id = node.get("id")
            graph[node_id] = {
                "node": node,
                "inputs": [],
                "outputs": []
            }
        
        # Add connections
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            
            if source in graph and target in graph:
                graph[source]["outputs"].append(target)
                graph[target]["inputs"].append(source)
        
        return graph
    
    def _find_start_node(self, nodes: List[Dict]) -> Optional[Dict]:
        """
        Find the UserQuery node (starting point)
        """
        for node in nodes:
            if node.get("type") == "UserQuery":
                return node
        return None
    
    async def _execute_node_sequence(
        self, 
        graph: Dict[str, Any], 
        start_node: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute nodes in sequence following the workflow path
        """
        current_data = input_data.copy()
        visited_nodes = set()
        
        # Start with UserQuery node
        node_id = start_node.get("id")
        current_data = await self._execute_single_node(start_node, current_data)
        visited_nodes.add(node_id)
        
        # Follow the execution path
        while True:
            # Find next node to execute
            next_nodes = graph.get(node_id, {}).get("outputs", [])
            
            if not next_nodes:
                break  # End of workflow
            
            # Execute all connected nodes (usually should be one)
            for next_node_id in next_nodes:
                if next_node_id not in visited_nodes:
                    next_node = graph[next_node_id]["node"]
                    current_data = await self._execute_single_node(next_node, current_data)
                    visited_nodes.add(next_node_id)
                    node_id = next_node_id
                    break
            else:
                break  # No more unvisited nodes
        
        return current_data
    
    async def _execute_single_node(
        self, 
        node: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single workflow component
        """
        node_type = node.get("type")
        node_data = node.get("data", {})
        
        logger.info(f"Executing node: {node_type}")
        
        if node_type == "UserQuery":
            return await self._execute_user_query(node_data, input_data)
        elif node_type == "KnowledgeBase":
            return await self._execute_knowledge_base(node_data, input_data)
        elif node_type == "LLMEngine":
            return await self._execute_llm_engine(node_data, input_data)
        elif node_type == "Output":
            return await self._execute_output(node_data, input_data)
        else:
            raise Exception(f"Unknown node type: {node_type}")
    
    async def _execute_user_query(
        self, 
        node_config: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute UserQuery component - Entry point for workflows
        """
        # Extract user query from input
        user_query = input_data.get("query", input_data.get("user_query", ""))
        
        if not user_query:
            raise Exception("No user query provided")
        
        result = input_data.copy()
        result["user_query"] = user_query
        result["timestamp"] = datetime.utcnow().isoformat()
        
        logger.info(f"UserQuery processed: {user_query[:100]}...")
        return result
    
    async def _execute_knowledge_base(
        self, 
        node_config: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute KnowledgeBase component - Document retrieval and context
        """
        user_query = input_data.get("user_query", "")
        
        # Get configuration
        document_ids = node_config.get("documents", [])
        similarity_threshold = node_config.get("similarity_threshold", 0.1)
        max_results = node_config.get("max_results", 5)
        
        try:
            # Generate query embedding
            query_embedding = await embedding_service.create_embedding(user_query)
            
            # Search for relevant document chunks
            query = select(DocumentChunk, Document).join(
                Document, DocumentChunk.document_id == Document.id
            ).where(
                Document.owner_id == self.user.id,
                DocumentChunk.embedding.isnot(None)
            )
            
            # Filter by specific documents if specified
            if document_ids:
                query = query.where(Document.id.in_(document_ids))
            
            result = await self.db.execute(query)
            chunks_with_docs = result.all()
            
            # Calculate similarities and sort
            relevant_chunks = []
            for chunk, document in chunks_with_docs:
                if chunk.embedding:
                    similarity = self._calculate_similarity(query_embedding, chunk.embedding)
                    if similarity >= similarity_threshold:
                        relevant_chunks.append({
                            "content": chunk.content,
                            "similarity": similarity,
                            "document_title": document.title,
                            "document_id": str(document.id)
                        })
            
            # Sort by similarity and limit results
            relevant_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            relevant_chunks = relevant_chunks[:max_results]
            
            # Prepare context
            context_content = [chunk["content"] for chunk in relevant_chunks]
            context_text = "\n\n".join(context_content)
            
            result = input_data.copy()
            result["knowledge_base_context"] = context_text
            result["relevant_chunks"] = relevant_chunks
            result["context_documents_count"] = len(relevant_chunks)
            
            logger.info(f"KnowledgeBase processed: Found {len(relevant_chunks)} relevant chunks")
            return result
            
        except Exception as e:
            logger.error(f"KnowledgeBase execution failed: {e}")
            result = input_data.copy()
            result["knowledge_base_context"] = ""
            result["error"] = f"Knowledge base search failed: {str(e)}"
            return result
    
    async def _execute_llm_engine(
        self, 
        node_config: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute LLMEngine component - AI processing
        """
        user_query = input_data.get("user_query", "")
        context = input_data.get("knowledge_base_context", "")
        
        # Get configuration
        model = node_config.get("model", "gemini-1.5-flash")
        temperature = node_config.get("temperature", 0.7)
        max_tokens = node_config.get("max_tokens", 2048)
        custom_prompt = node_config.get("custom_prompt", "")
        use_web_search = node_config.get("use_web_search", False)
        
        try:
            # Build prompt
            prompt_parts = []
            
            if custom_prompt:
                prompt_parts.append(f"Instructions: {custom_prompt}")
            
            if context:
                prompt_parts.append(f"Context from documents:\n{context}")
            
            prompt_parts.append(f"User Question: {user_query}")
            
            if not context:
                prompt_parts.append(
                    "Please provide a helpful response based on your knowledge. "
                    "If you need additional context, please let the user know."
                )
            
            final_prompt = "\n\n".join(prompt_parts)
            
            # Generate response
            if context:
                ai_response = await gemini_service.chat_with_context(user_query, [context])
            else:
                ai_response = await gemini_service.generate_text(final_prompt)
            
            result = input_data.copy()
            result["llm_response"] = ai_response
            result["model_used"] = model
            result["prompt_tokens"] = len(final_prompt.split())
            
            logger.info(f"LLMEngine processed: Generated response ({len(ai_response)} chars)")
            return result
            
        except Exception as e:
            logger.error(f"LLMEngine execution failed: {e}")
            result = input_data.copy()
            result["llm_response"] = f"I apologize, but I encountered an error while processing your request: {str(e)}"
            result["error"] = str(e)
            return result
    
    async def _execute_output(
        self, 
        node_config: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Output component - Format and return final response
        """
        # Get configuration
        output_format = node_config.get("format", "text")
        include_sources = node_config.get("include_sources", True)
        
        llm_response = input_data.get("llm_response", "No response generated")
        relevant_chunks = input_data.get("relevant_chunks", [])
        
        # Format output
        if output_format == "json":
            output = {
                "answer": llm_response,
                "sources": relevant_chunks if include_sources else [],
                "metadata": {
                    "context_documents_count": input_data.get("context_documents_count", 0),
                    "model_used": input_data.get("model_used", "unknown"),
                    "timestamp": input_data.get("timestamp")
                }
            }
        else:
            # Text format
            output_parts = [llm_response]
            
            if include_sources and relevant_chunks:
                output_parts.append("\n\nSources:")
                for i, chunk in enumerate(relevant_chunks[:3], 1):
                    output_parts.append(
                        f"{i}. {chunk['document_title']} (similarity: {chunk['similarity']:.2f})"
                    )
            
            output = "\n".join(output_parts)
        
        result = input_data.copy()
        result["final_output"] = output
        result["answer"] = llm_response  # Add answer field for API compatibility
        result["output_format"] = output_format
        
        logger.info(f"Output processed: Generated final response")
        return result
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        try:
            import numpy as np
            
            a = np.array(vec1)
            b = np.array(vec2)
            
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
        except Exception:
            return 0.0

# Legacy function for backward compatibility
def run_workflow(workflow_definition: dict, user_query: str, custom_prompt: str = None):
    """
    Legacy function - use WorkflowEngine class instead
    """
    # Simple fallback implementation
    try:
        from app.services.gemini_service import gemini_service
        import asyncio
        
        nodes = workflow_definition.get("nodes", [])
        has_kb = any(n.get("type") == "KnowledgeBase" for n in nodes)
        
        if has_kb:
            # Simple context retrieval would go here
            context = "Context from documents would be retrieved here"
            prompt = f"Context: {context}\n\nUser Query: {user_query}"
        else:
            prompt = user_query
        
        if custom_prompt:
            prompt = f"{custom_prompt}\n\n{prompt}"
        
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(gemini_service.generate_text(prompt))
        finally:
            loop.close()
        
        return response
        
    except Exception as e:
        return f"Workflow execution failed: {str(e)}"
