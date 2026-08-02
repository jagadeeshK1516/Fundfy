"""Communication API routes."""

from fastapi import APIRouter

from fundfy.api.schemas import CommunicationSessionRequest, CommunicationSessionResponse
from fundfy.communication.modes import ConversationMode
from fundfy.communication.session import CommunicationSession

router = APIRouter(prefix="/api", tags=["communication"])

# In-memory session store
_sessions: dict[str, CommunicationSession] = {}


@router.post("/communication/session", response_model=CommunicationSessionResponse)
async def communication_session(request: CommunicationSessionRequest):
    """Start or continue a communication session."""
    from fundfy.dependencies import get_agent_llm

    llm = get_agent_llm()
    mode = ConversationMode(request.mode)

    session_key = f"{request.founder_id}:{request.mode}"

    if session_key not in _sessions:
        _sessions[session_key] = CommunicationSession(
            founder_id=request.founder_id,
            mode=mode,
            llm=llm,
        )
    else:
        session = _sessions[session_key]
        if session.mode != mode:
            session.switch_mode(mode)

    session = _sessions[session_key]
    response = await session.send_message(request.message)

    return CommunicationSessionResponse(
        founder_id=request.founder_id,
        mode=request.mode,
        response=response,
    )
