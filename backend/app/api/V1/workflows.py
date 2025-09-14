from fastapi import APIRouter, Body
from app.services.workflow_engine import run_workflow

router = APIRouter(prefix="/workflow", tags=["workflow"])

@router.post("/run")
async def run_workflow_endpoint(definition: dict = Body(...), query: str = Body(...), custom_prompt: str = Body(None)):
    # basic validation
    types = [n.get("type") for n in definition.get("nodes", [])]
    if "UserQuery" not in types:
        return {"error": "Workflow must include a UserQuery node"}
    # Execute
    resp = run_workflow(definition, user_query=query, custom_prompt=custom_prompt)
    return {"answer": resp}
