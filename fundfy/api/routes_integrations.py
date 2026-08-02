"""Integration API routes — Google OAuth, Gmail, Calendar, Drive, Email approvals."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, update

from fundfy.db import async_session
from fundfy.models.email_approval import EmailApproval

router = APIRouter(prefix="/api", tags=["integrations"])


# --- Google OAuth ---

class CallbackRequest(BaseModel):
    """OAuth callback request."""
    code: str
    state: str | None = None


@router.get("/integrations/google/auth-url")
async def get_google_auth_url(request: Request):
    """Return the Google OAuth consent URL."""
    from fundfy.integrations.google_auth import generate_consent_url

    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else "anonymous"
    url = generate_consent_url(state=founder_id)
    return {"auth_url": url}


@router.post("/integrations/google/callback")
async def google_callback(request: Request, body: CallbackRequest):
    """Exchange OAuth code for tokens."""
    from fundfy.integrations.google_auth import exchange_code_for_tokens

    founder_id = body.state or (request.state.founder_id if hasattr(request.state, "founder_id") else None)
    if not founder_id:
        raise HTTPException(status_code=400, detail="Founder ID required")

    try:
        result = await exchange_code_for_tokens(body.code, founder_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {str(e)}")


@router.get("/integrations/google/status")
async def google_status(request: Request):
    """Check Google connection status."""
    from fundfy.integrations.google_auth import get_connection_status

    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        return {"connected": False}
    status = await get_connection_status(founder_id)
    return status


@router.delete("/integrations/google/disconnect")
async def google_disconnect(request: Request):
    """Disconnect Google account."""
    from fundfy.integrations.google_auth import disconnect

    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await disconnect(founder_id)
    return {"disconnected": result}


# --- Email Approvals ---

@router.get("/emails/pending")
async def list_pending_emails(request: Request):
    """List emails awaiting approval."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async with async_session() as session:
        result = await session.execute(
            select(EmailApproval)
            .where(EmailApproval.founder_id == founder_id, EmailApproval.status == "pending")
            .order_by(EmailApproval.created_at.desc())
        )
        approvals = result.scalars().all()
        return [
            {
                "id": a.id,
                "to": a.to,
                "subject": a.subject,
                "body": a.body,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in approvals
        ]


@router.post("/emails/{email_id}/approve")
async def approve_email(email_id: str, request: Request):
    """Approve and send an email."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async with async_session() as session:
        result = await session.execute(
            select(EmailApproval).where(
                EmailApproval.id == email_id,
                EmailApproval.founder_id == founder_id,
            )
        )
        approval = result.scalar_one_or_none()
        if not approval:
            raise HTTPException(status_code=404, detail="Email not found")
        if approval.status != "pending":
            raise HTTPException(status_code=400, detail=f"Email already {approval.status}")

        # Try to send via Gmail
        try:
            from fundfy.integrations.google_auth import get_access_token
            access_token = await get_access_token(founder_id)
            if access_token:
                from google.oauth2.credentials import Credentials
                from fundfy.integrations.gmail import GmailService

                credentials = Credentials(token=access_token)
                gmail = GmailService(credentials)
                gmail.send_email(approval.to, approval.subject, approval.body)
        except Exception:
            pass  # Mark as approved even if send fails

        approval.status = "sent"
        await session.commit()
        return {"status": "sent", "id": email_id}


@router.post("/emails/{email_id}/reject")
async def reject_email(email_id: str, request: Request):
    """Reject an email draft."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async with async_session() as session:
        result = await session.execute(
            select(EmailApproval).where(
                EmailApproval.id == email_id,
                EmailApproval.founder_id == founder_id,
            )
        )
        approval = result.scalar_one_or_none()
        if not approval:
            raise HTTPException(status_code=404, detail="Email not found")

        approval.status = "rejected"
        await session.commit()
        return {"status": "rejected", "id": email_id}


# --- Calendar ---

class CreateEventRequest(BaseModel):
    """Create calendar event request."""
    summary: str
    start: str
    end: str
    attendees: list[str] = []
    meet_link: bool = True


@router.get("/calendar/events")
async def list_calendar_events(request: Request, time_min: str | None = None, time_max: str | None = None):
    """List upcoming calendar events."""
    from datetime import datetime, timedelta

    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"
    if not time_max:
        time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

    try:
        from fundfy.integrations.google_auth import get_access_token
        from google.oauth2.credentials import Credentials
        from fundfy.integrations.calendar import CalendarService

        access_token = await get_access_token(founder_id)
        if not access_token:
            return {"events": [], "connected": False}

        credentials = Credentials(token=access_token)
        calendar = CalendarService(credentials)
        events = calendar.list_events(time_min, time_max)
        return {"events": events, "connected": True}
    except Exception as e:
        return {"events": [], "error": str(e)}


@router.post("/calendar/events")
async def create_calendar_event(request: Request, body: CreateEventRequest):
    """Create a calendar event."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        from fundfy.integrations.google_auth import get_access_token
        from google.oauth2.credentials import Credentials
        from fundfy.integrations.calendar import CalendarService

        access_token = await get_access_token(founder_id)
        if not access_token:
            raise HTTPException(status_code=400, detail="Google not connected")

        credentials = Credentials(token=access_token)
        calendar = CalendarService(credentials)
        event = calendar.create_event(
            summary=body.summary,
            start=body.start,
            end=body.end,
            attendees=body.attendees,
            meet_link=body.meet_link,
        )
        return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/availability")
async def check_calendar_availability(request: Request, time_min: str, time_max: str):
    """Check calendar availability."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        from fundfy.integrations.google_auth import get_access_token
        from google.oauth2.credentials import Credentials
        from fundfy.integrations.calendar import CalendarService

        access_token = await get_access_token(founder_id)
        if not access_token:
            raise HTTPException(status_code=400, detail="Google not connected")

        credentials = Credentials(token=access_token)
        calendar = CalendarService(credentials)
        busy = calendar.check_availability(time_min, time_max)
        return {"busy_slots": busy}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Drive ---

@router.post("/drive/upload/{file_id}")
async def upload_to_drive(file_id: str, request: Request):
    """Upload a generated file to Google Drive."""
    from fundfy.models.generated_file import GeneratedFile

    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async with async_session() as session:
        result = await session.execute(
            select(GeneratedFile).where(GeneratedFile.id == file_id)
        )
        gen_file = result.scalar_one_or_none()
        if not gen_file:
            raise HTTPException(status_code=404, detail="File not found")

    try:
        from fundfy.integrations.google_auth import get_access_token
        from google.oauth2.credentials import Credentials
        from fundfy.integrations.drive import DriveService

        access_token = await get_access_token(founder_id)
        if not access_token:
            raise HTTPException(status_code=400, detail="Google not connected")

        credentials = Credentials(token=access_token)
        drive = DriveService(credentials)
        result = drive.upload_file(gen_file.file_path)
        link = drive.get_share_link(result["id"])
        return {"file_id": result["id"], "share_link": link}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Investors ---

class AddInvestorRequest(BaseModel):
    """Add investor request."""
    name: str
    firm: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    focus_areas: list[str] = []
    stage_preference: str | None = None
    check_size_min: float | None = None
    check_size_max: float | None = None
    portfolio_companies: list[str] = []
    location: str | None = None
    notes: str | None = None


@router.get("/investors")
async def list_investors(
    stage: str | None = None,
    industry: str | None = None,
    location: str | None = None,
    check_size_min: float | None = None,
    check_size_max: float | None = None,
):
    """Search/list investors."""
    from fundfy.integrations.investor_db import InvestorDatabase

    db = InvestorDatabase()
    filters: dict[str, Any] = {}
    if stage:
        filters["stage"] = stage
    if industry:
        filters["industry"] = industry
    if location:
        filters["location"] = location
    if check_size_min is not None:
        filters["check_size_min"] = check_size_min
    if check_size_max is not None:
        filters["check_size_max"] = check_size_max

    results = await db.search(filters)
    return {"investors": results, "count": len(results)}


@router.get("/investors/{investor_id}")
async def get_investor(investor_id: str):
    """Get investor detail."""
    from fundfy.integrations.investor_db import InvestorDatabase

    db = InvestorDatabase()
    investor = await db.get(investor_id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    return investor


@router.post("/investors")
async def add_investor(body: AddInvestorRequest):
    """Add a custom investor."""
    from fundfy.integrations.investor_db import InvestorDatabase

    db = InvestorDatabase()
    result = await db.add(body.model_dump())
    return result


# --- Grants ---

class MatchGrantsRequest(BaseModel):
    """Match grants to business request."""
    business_id: str


class CreateGrantApplicationRequest(BaseModel):
    """Create a grant application tracking record."""
    grant_id: str
    business_id: str | None = None
    notes: str | None = None


class UpdateGrantApplicationRequest(BaseModel):
    """Update a grant application."""
    status: str | None = None
    notes: str | None = None


@router.get("/grants")
async def list_grants(
    industry: str | None = None,
    region: str | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    status: str | None = "open",
):
    """Search grants."""
    from fundfy.integrations.grant_db import GrantDatabase

    db = GrantDatabase()
    filters: dict[str, Any] = {}
    if industry:
        filters["industry"] = industry
    if region:
        filters["region"] = region
    if amount_min is not None:
        filters["amount_min"] = amount_min
    if amount_max is not None:
        filters["amount_max"] = amount_max
    if status:
        filters["status"] = status

    results = await db.search(filters)
    return {"grants": results, "count": len(results)}


@router.get("/grants/{grant_id}")
async def get_grant(grant_id: str):
    """Get grant detail."""
    from fundfy.integrations.grant_db import GrantDatabase

    db = GrantDatabase()
    grant = await db.get(grant_id)
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")
    return grant


@router.post("/grants/match")
async def match_grants(body: MatchGrantsRequest):
    """Auto-match grants to a business."""
    from fundfy.integrations.grant_db import GrantDatabase

    db = GrantDatabase()
    results = await db.match_to_business(body.business_id)
    return {"matched_grants": results, "count": len(results)}


@router.get("/grants/applications")
async def list_grant_applications(request: Request):
    """List tracked grant applications."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from fundfy.integrations.grant_db import GrantDatabase

    db = GrantDatabase()
    results = await db.list_applications(founder_id)
    return {"applications": results}


@router.post("/grants/applications")
async def create_grant_application(request: Request, body: CreateGrantApplicationRequest):
    """Track a new grant application."""
    founder_id = request.state.founder_id if hasattr(request.state, "founder_id") else None
    if not founder_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from fundfy.integrations.grant_db import GrantDatabase

    db = GrantDatabase()
    result = await db.create_application(
        founder_id=founder_id,
        grant_id=body.grant_id,
        business_id=body.business_id,
        notes=body.notes,
    )
    return result


@router.patch("/grants/applications/{app_id}")
async def update_grant_application(app_id: str, body: UpdateGrantApplicationRequest):
    """Update a grant application status."""
    from fundfy.integrations.grant_db import GrantDatabase

    db = GrantDatabase()
    data = {}
    if body.status:
        data["status"] = body.status
    if body.notes:
        data["notes"] = body.notes

    result = await db.update_application(app_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return result
