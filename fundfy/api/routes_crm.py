"""CRM API routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from fundfy.integrations.crm import CRMService

router = APIRouter(prefix="/api/crm", tags=["crm"])

_crm = CRMService()


class AddContactRequest(BaseModel):
    """Add contact request."""
    name: str
    email: str | None = None
    company: str | None = None
    role: str | None = None
    type: str = "other"
    pipeline_stage: str = "lead"
    notes: str | None = None


class UpdateContactRequest(BaseModel):
    """Update contact request."""
    name: str | None = None
    email: str | None = None
    company: str | None = None
    role: str | None = None
    type: str | None = None
    pipeline_stage: str | None = None
    notes: str | None = None


class LogInteractionRequest(BaseModel):
    """Log interaction request."""
    type: str = "note"
    summary: str
    details: str | None = None
    occurred_at: str | None = None


@router.get("/contacts")
async def list_contacts(
    request: Request,
    type: str | None = None,
    pipeline_stage: str | None = None,
    query: str | None = None,
):
    """List/search CRM contacts."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    filters = {}
    if type:
        filters["type"] = type
    if pipeline_stage:
        filters["pipeline_stage"] = pipeline_stage
    if query:
        filters["query"] = query

    contacts = await _crm.search_contacts(founder_id, filters)
    return {"contacts": contacts, "count": len(contacts)}


@router.post("/contacts")
async def add_contact(request: Request, body: AddContactRequest):
    """Add a new CRM contact."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await _crm.add_contact(founder_id, body.model_dump())
    return result


@router.patch("/contacts/{contact_id}")
async def update_contact(contact_id: str, body: UpdateContactRequest):
    """Update a CRM contact."""
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await _crm.update_contact(contact_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")
    return result


@router.get("/contacts/{contact_id}/interactions")
async def get_interactions(contact_id: str):
    """Get interactions for a contact."""
    interactions = await _crm.get_interactions(contact_id)
    return {"interactions": interactions}


@router.post("/contacts/{contact_id}/interactions")
async def log_interaction(contact_id: str, request: Request, body: LogInteractionRequest):
    """Log an interaction with a contact."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    data = body.model_dump(exclude_none=True)
    result = await _crm.log_interaction(contact_id, founder_id, data)
    return result


@router.get("/pipeline")
async def get_pipeline(request: Request):
    """Get pipeline summary (counts per stage)."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    summary = await _crm.get_pipeline_summary(founder_id)
    return {"pipeline": summary}
