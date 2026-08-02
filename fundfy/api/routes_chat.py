"""Chat API routes."""

from fastapi import APIRouter, Depends

from fundfy.api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main conversational endpoint."""
    from fundfy.dependencies import get_agent

    agent = get_agent()
    result = await agent.chat_with_metadata(request.founder_id, request.message)

    return ChatResponse(
        response=result["response"],
        founder_id=request.founder_id,
        tool_calls=result.get("tool_calls"),
        steps=result.get("steps"),
        checkpoints=result.get("checkpoints"),
        files=result.get("files"),
    )
