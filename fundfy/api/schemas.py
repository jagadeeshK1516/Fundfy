"""Pydantic request/response schemas for API endpoints."""

from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Chat message request."""

    founder_id: str
    message: str


class ChatResponse(BaseModel):
    """Chat message response."""

    response: str
    founder_id: str
    tool_calls: list[dict] | None = None
    steps: int | None = None
    checkpoints: list[dict] | None = None
    files: list[dict] | None = None


class BusinessCreate(BaseModel):
    """Create a new business."""

    founder_id: str
    name: str
    industry: str | None = None
    stage: str | None = None
    goals_json: str | None = None


class BusinessResponse(BaseModel):
    """Business details response."""

    id: str
    founder_id: str
    name: str
    industry: str | None = None
    stage: str | None = None
    goals_json: str | None = None
    created_at: datetime | None = None


class ExecutionRequest(BaseModel):
    """Execution plan request."""

    business_id: str
    objective: str
    context: str | None = None


class ExecutionResponse(BaseModel):
    """Execution plan response."""

    business_id: str
    tasks: list[dict]
    status: str
    job_id: str | None = None


class DocumentGenerateRequest(BaseModel):
    """Document generation request."""

    business_id: str
    doc_type: str
    context: str | None = None


class DocumentResponse(BaseModel):
    """Document response."""

    id: str | None = None
    business_id: str
    doc_type: str
    title: str
    content: str
    job_id: str | None = None


class WorkstreamResponse(BaseModel):
    """Workstream task response."""

    id: str
    business_id: str
    type: str
    status: str
    params_json: str | None = None
    result_json: str | None = None


class CommunicationSessionRequest(BaseModel):
    """Communication session request."""

    founder_id: str
    mode: str = "chat"
    message: str


class CommunicationSessionResponse(BaseModel):
    """Communication session response."""

    founder_id: str
    mode: str
    response: str
