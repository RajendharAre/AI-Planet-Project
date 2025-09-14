from app.services.chroma_client import get_chroma_client, get_collection
from app.services.embeddings_service import create_openai_embedding
from app.core.config import settings
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

# Check if we have a valid OpenAI API key
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
        openai_client = None
else:
    logger.warning("No valid OpenAI API key found. LLM functionality will use dummy responses.")
    openai_client = None

def retrieve_context_from_kb(query: str, k=4):
    client = get_chroma_client()
    col = get_collection(client)
    q_emb = create_openai_embedding(query)
    results = col.query(query_embeddings=[q_emb], n_results=k, include=["documents", "metadatas", "distances"])
    # results["documents"] is list of list
    docs = [d for sub in results["documents"] for d in sub]
    metadatas = [m for sub in results["metadatas"] for m in sub]
    return docs, metadatas

def call_llm_system(prompt: str, system_message: str = None):
    """Call LLM with fallback for when OpenAI is not available"""
    if has_openai_key and openai_client:
        try:
            messages = []
            if system_message:
                messages.append({"role":"system", "content": system_message})
            messages.append({"role":"user", "content": prompt})
            resp = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages, max_tokens=800)
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return f"I apologize, but I'm currently unable to process your request due to an AI service issue. Your query was: {prompt[:100]}..."
    else:
        # Return a dummy response when OpenAI is not available
        return f"This is a test response to your query: '{prompt[:100]}...'. To get real AI responses, please configure a valid OpenAI API key in the .env file."

def run_workflow(workflow_definition: dict, user_query: str, custom_prompt: str = None):
    """
    Very simple orchestrator:
    - Workflow is nodes + edges. We assume nodes are ordered logically or use node types.
    - For now support: UserQuery -> (optional KnowledgeBase) -> LLM -> Output
    """
    # Determine if KB node exists (by type)
    nodes = workflow_definition.get("nodes", [])
    has_kb = any(n.get("type") == "KnowledgeBase" for n in nodes)
    context = ""
    if has_kb:
        docs, metas = retrieve_context_from_kb(user_query)
        context = "\n\n".join(docs)

    # Build prompt
    prompt_parts = []
    if context:
        prompt_parts.append("Context from KnowledgeBase:\n" + context)
    prompt_parts.append("User query:\n" + user_query)
    if custom_prompt:
        prompt_parts.append("Custom prompt:\n" + custom_prompt)

    final_prompt = "\n\n".join(prompt_parts)
    answer = call_llm_system(final_prompt)
    return answer
