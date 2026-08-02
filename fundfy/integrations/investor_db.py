"""Investor database service."""

import json
import os
import uuid
from typing import Any

from sqlalchemy import select

from fundfy.db import async_session
from fundfy.models.investor import Investor


class InvestorDatabase:
    """Manages the investor database with search and CRUD."""

    async def search(self, filters: dict[str, Any] | None = None) -> list[dict]:
        """Search investors with optional filters (stage, industry, check_size, location)."""
        filters = filters or {}
        async with async_session() as session:
            query = select(Investor)

            if "stage" in filters and filters["stage"]:
                query = query.where(Investor.stage_preference == filters["stage"])
            if "location" in filters and filters["location"]:
                query = query.where(Investor.location.ilike(f"%{filters['location']}%"))
            if "check_size_min" in filters and filters["check_size_min"] is not None:
                query = query.where(Investor.check_size_max >= filters["check_size_min"])
            if "check_size_max" in filters and filters["check_size_max"] is not None:
                query = query.where(Investor.check_size_min <= filters["check_size_max"])

            result = await session.execute(query)
            investors = result.scalars().all()

            results = []
            for inv in investors:
                inv_dict = self._to_dict(inv)
                # Filter by industry (focus_areas is JSON)
                if "industry" in filters and filters["industry"]:
                    focus_areas = json.loads(inv.focus_areas) if inv.focus_areas else []
                    if not any(filters["industry"].lower() in a.lower() for a in focus_areas):
                        continue
                results.append(inv_dict)

            return results

    async def get(self, investor_id: str) -> dict | None:
        """Get an investor by ID."""
        async with async_session() as session:
            result = await session.execute(
                select(Investor).where(Investor.id == investor_id)
            )
            inv = result.scalar_one_or_none()
            return self._to_dict(inv) if inv else None

    async def add(self, profile: dict[str, Any]) -> dict:
        """Add an investor to the database."""
        async with async_session() as session:
            investor = Investor(
                id=profile.get("id", str(uuid.uuid4())),
                name=profile["name"],
                firm=profile.get("firm"),
                email=profile.get("email"),
                linkedin_url=profile.get("linkedin_url"),
                focus_areas=json.dumps(profile.get("focus_areas", [])),
                stage_preference=profile.get("stage_preference"),
                check_size_min=profile.get("check_size_min"),
                check_size_max=profile.get("check_size_max"),
                portfolio_companies=json.dumps(profile.get("portfolio_companies", [])),
                location=profile.get("location"),
                notes=profile.get("notes"),
            )
            session.add(investor)
            await session.commit()
            await session.refresh(investor)
            return self._to_dict(investor)

    async def update(self, investor_id: str, data: dict[str, Any]) -> dict | None:
        """Update an investor."""
        async with async_session() as session:
            result = await session.execute(
                select(Investor).where(Investor.id == investor_id)
            )
            investor = result.scalar_one_or_none()
            if not investor:
                return None
            for key, value in data.items():
                if key in ("focus_areas", "portfolio_companies") and isinstance(value, list):
                    setattr(investor, key, json.dumps(value))
                elif hasattr(investor, key):
                    setattr(investor, key, value)
            await session.commit()
            await session.refresh(investor)
            return self._to_dict(investor)

    async def seed_from_file(self) -> int:
        """Seed the database from the investors.json seed file."""
        seed_path = os.path.join(os.path.dirname(__file__), "seed_data", "investors.json")
        if not os.path.exists(seed_path):
            return 0
        with open(seed_path, "r") as f:
            investors = json.load(f)

        count = 0
        for profile in investors:
            # Check if already exists
            async with async_session() as session:
                result = await session.execute(
                    select(Investor).where(Investor.name == profile["name"])
                )
                if result.scalar_one_or_none():
                    continue
            await self.add(profile)
            count += 1
        return count

    def _to_dict(self, investor: Investor) -> dict:
        """Convert an Investor model to a dictionary."""
        return {
            "id": investor.id,
            "name": investor.name,
            "firm": investor.firm,
            "email": investor.email,
            "linkedin_url": investor.linkedin_url,
            "focus_areas": json.loads(investor.focus_areas) if investor.focus_areas else [],
            "stage_preference": investor.stage_preference,
            "check_size_min": investor.check_size_min,
            "check_size_max": investor.check_size_max,
            "portfolio_companies": json.loads(investor.portfolio_companies) if investor.portfolio_companies else [],
            "location": investor.location,
            "notes": investor.notes,
            "created_at": investor.created_at.isoformat() if investor.created_at else None,
        }
