"""Grant database service."""

import json
import os
import uuid
from typing import Any

from sqlalchemy import select

from fundfy.db import async_session
from fundfy.models.grant import Grant
from fundfy.models.grant_application import GrantApplication


class GrantDatabase:
    """Manages the grant database with search, CRUD, and matching."""

    async def search(self, filters: dict[str, Any] | None = None) -> list[dict]:
        """Search grants with optional filters (industry, amount, deadline, status)."""
        filters = filters or {}
        async with async_session() as session:
            query = select(Grant)

            if "status" in filters and filters["status"]:
                query = query.where(Grant.status == filters["status"])
            if "region" in filters and filters["region"]:
                query = query.where(Grant.region.ilike(f"%{filters['region']}%"))
            if "amount_min" in filters and filters["amount_min"] is not None:
                query = query.where(Grant.amount_max >= filters["amount_min"])
            if "amount_max" in filters and filters["amount_max"] is not None:
                query = query.where(Grant.amount_min <= filters["amount_max"])

            result = await session.execute(query)
            grants = result.scalars().all()

            results = []
            for grant in grants:
                grant_dict = self._to_dict(grant)
                # Filter by industry
                if "industry" in filters and filters["industry"]:
                    focus = json.loads(grant.industry_focus) if grant.industry_focus else []
                    if not any(filters["industry"].lower() in f.lower() for f in focus):
                        continue
                results.append(grant_dict)

            return results

    async def get(self, grant_id: str) -> dict | None:
        """Get a grant by ID."""
        async with async_session() as session:
            result = await session.execute(
                select(Grant).where(Grant.id == grant_id)
            )
            grant = result.scalar_one_or_none()
            return self._to_dict(grant) if grant else None

    async def add(self, grant_data: dict[str, Any]) -> dict:
        """Add a grant to the database."""
        async with async_session() as session:
            grant = Grant(
                id=grant_data.get("id", str(uuid.uuid4())),
                name=grant_data["name"],
                provider=grant_data["provider"],
                amount_min=grant_data.get("amount_min"),
                amount_max=grant_data.get("amount_max"),
                deadline=grant_data.get("deadline"),
                eligibility_criteria=json.dumps(grant_data.get("eligibility_criteria", [])),
                industry_focus=json.dumps(grant_data.get("industry_focus", [])),
                application_url=grant_data.get("application_url"),
                description=grant_data.get("description"),
                region=grant_data.get("region"),
                status=grant_data.get("status", "open"),
            )
            session.add(grant)
            await session.commit()
            await session.refresh(grant)
            return self._to_dict(grant)

    async def match_to_business(self, business_id: str) -> list[dict]:
        """Auto-match grants based on business industry. Returns matching grants."""
        from fundfy.models.business import Business

        async with async_session() as session:
            result = await session.execute(
                select(Business).where(Business.id == business_id)
            )
            business = result.scalar_one_or_none()
            if not business:
                return []

        industry = business.industry if business else ""
        return await self.search({"industry": industry, "status": "open"})

    async def seed_from_file(self) -> int:
        """Seed the database from the grants.json seed file."""
        seed_path = os.path.join(os.path.dirname(__file__), "seed_data", "grants.json")
        if not os.path.exists(seed_path):
            return 0
        with open(seed_path, "r") as f:
            grants = json.load(f)

        count = 0
        for grant_data in grants:
            async with async_session() as session:
                result = await session.execute(
                    select(Grant).where(Grant.name == grant_data["name"])
                )
                if result.scalar_one_or_none():
                    continue
            await self.add(grant_data)
            count += 1
        return count

    # Grant application tracking
    async def create_application(self, founder_id: str, grant_id: str, business_id: str | None = None, notes: str | None = None) -> dict:
        """Track a new grant application."""
        async with async_session() as session:
            app = GrantApplication(
                id=str(uuid.uuid4()),
                founder_id=founder_id,
                grant_id=grant_id,
                business_id=business_id,
                status="discovered",
                notes=notes,
            )
            session.add(app)
            await session.commit()
            await session.refresh(app)
            return self._app_to_dict(app)

    async def update_application(self, app_id: str, data: dict[str, Any]) -> dict | None:
        """Update a grant application status."""
        async with async_session() as session:
            result = await session.execute(
                select(GrantApplication).where(GrantApplication.id == app_id)
            )
            app = result.scalar_one_or_none()
            if not app:
                return None
            for key, value in data.items():
                if hasattr(app, key):
                    setattr(app, key, value)
            await session.commit()
            await session.refresh(app)
            return self._app_to_dict(app)

    async def list_applications(self, founder_id: str) -> list[dict]:
        """List all grant applications for a founder."""
        async with async_session() as session:
            result = await session.execute(
                select(GrantApplication).where(GrantApplication.founder_id == founder_id)
            )
            apps = result.scalars().all()
            return [self._app_to_dict(a) for a in apps]

    def _to_dict(self, grant: Grant) -> dict:
        """Convert a Grant model to a dictionary."""
        return {
            "id": grant.id,
            "name": grant.name,
            "provider": grant.provider,
            "amount_min": grant.amount_min,
            "amount_max": grant.amount_max,
            "deadline": grant.deadline,
            "eligibility_criteria": json.loads(grant.eligibility_criteria) if grant.eligibility_criteria else [],
            "industry_focus": json.loads(grant.industry_focus) if grant.industry_focus else [],
            "application_url": grant.application_url,
            "description": grant.description,
            "region": grant.region,
            "status": grant.status,
            "created_at": grant.created_at.isoformat() if grant.created_at else None,
        }

    def _app_to_dict(self, app: GrantApplication) -> dict:
        """Convert a GrantApplication model to a dictionary."""
        return {
            "id": app.id,
            "founder_id": app.founder_id,
            "grant_id": app.grant_id,
            "business_id": app.business_id,
            "status": app.status,
            "notes": app.notes,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "created_at": app.created_at.isoformat() if app.created_at else None,
        }
