"""Business API routes."""

import uuid

from fastapi import APIRouter

from fundfy.api.schemas import BusinessCreate, BusinessResponse

router = APIRouter(prefix="/api", tags=["business"])

# In-memory store for MVP (will be replaced with DB in integration step)
_businesses: dict[str, dict] = {}


@router.post("/business", response_model=BusinessResponse)
async def create_business(request: BusinessCreate):
    """Create a new business profile."""
    business_id = str(uuid.uuid4())
    business = {
        "id": business_id,
        "founder_id": request.founder_id,
        "name": request.name,
        "industry": request.industry,
        "stage": request.stage,
        "goals_json": request.goals_json,
        "created_at": None,
    }
    _businesses[business_id] = business
    return BusinessResponse(**business)


@router.get("/business/{business_id}", response_model=BusinessResponse)
async def get_business(business_id: str):
    """Get a business profile by ID."""
    business = _businesses.get(business_id)
    if not business:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Business not found")
    return BusinessResponse(**business)
