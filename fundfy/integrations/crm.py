"""Built-in CRM service."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, func

from fundfy.db import async_session
from fundfy.models.crm import Contact, Interaction


class CRMService:
    """CRM service for managing contacts and interactions."""

    async def add_contact(self, founder_id: str, data: dict[str, Any]) -> dict:
        """Add a new contact."""
        async with async_session() as session:
            contact = Contact(
                id=str(uuid.uuid4()),
                founder_id=founder_id,
                name=data["name"],
                email=data.get("email"),
                company=data.get("company"),
                role=data.get("role"),
                type=data.get("type", "other"),
                pipeline_stage=data.get("pipeline_stage", "lead"),
                notes=data.get("notes"),
            )
            session.add(contact)
            await session.commit()
            await session.refresh(contact)
            return self._contact_to_dict(contact)

    async def update_contact(self, contact_id: str, data: dict[str, Any]) -> dict | None:
        """Update a contact."""
        async with async_session() as session:
            result = await session.execute(
                select(Contact).where(Contact.id == contact_id)
            )
            contact = result.scalar_one_or_none()
            if not contact:
                return None
            for key, value in data.items():
                if hasattr(contact, key) and key not in ("id", "founder_id", "created_at"):
                    setattr(contact, key, value)
            await session.commit()
            await session.refresh(contact)
            return self._contact_to_dict(contact)

    async def move_stage(self, contact_id: str, stage: str) -> dict | None:
        """Move a contact to a different pipeline stage."""
        return await self.update_contact(contact_id, {"pipeline_stage": stage})

    async def log_interaction(self, contact_id: str, founder_id: str, data: dict[str, Any]) -> dict:
        """Log an interaction with a contact."""
        async with async_session() as session:
            interaction = Interaction(
                id=str(uuid.uuid4()),
                contact_id=contact_id,
                founder_id=founder_id,
                type=data.get("type", "note"),
                summary=data["summary"],
                details=data.get("details"),
                occurred_at=datetime.fromisoformat(data["occurred_at"]) if "occurred_at" in data else datetime.utcnow(),
            )
            session.add(interaction)

            # Update last_contacted_at on the contact
            result = await session.execute(
                select(Contact).where(Contact.id == contact_id)
            )
            contact = result.scalar_one_or_none()
            if contact:
                contact.last_contacted_at = interaction.occurred_at

            await session.commit()
            await session.refresh(interaction)
            return self._interaction_to_dict(interaction)

    async def get_pipeline_summary(self, founder_id: str) -> dict[str, int]:
        """Get counts per pipeline stage."""
        stages = ["lead", "contacted", "meeting", "proposal", "negotiation", "closed_won", "closed_lost"]
        async with async_session() as session:
            result = await session.execute(
                select(Contact.pipeline_stage, func.count(Contact.id))
                .where(Contact.founder_id == founder_id)
                .group_by(Contact.pipeline_stage)
            )
            counts = {stage: 0 for stage in stages}
            for stage, count in result.all():
                counts[stage] = count
            return counts

    async def search_contacts(self, founder_id: str, filters: dict[str, Any] | None = None) -> list[dict]:
        """Search contacts with optional filters."""
        filters = filters or {}
        async with async_session() as session:
            query = select(Contact).where(Contact.founder_id == founder_id)

            if "type" in filters and filters["type"]:
                query = query.where(Contact.type == filters["type"])
            if "pipeline_stage" in filters and filters["pipeline_stage"]:
                query = query.where(Contact.pipeline_stage == filters["pipeline_stage"])
            if "query" in filters and filters["query"]:
                q = f"%{filters['query']}%"
                query = query.where(
                    Contact.name.ilike(q) | Contact.company.ilike(q) | Contact.email.ilike(q)
                )

            query = query.order_by(Contact.created_at.desc())
            result = await session.execute(query)
            contacts = result.scalars().all()
            return [self._contact_to_dict(c) for c in contacts]

    async def get_contact(self, contact_id: str) -> dict | None:
        """Get a contact by ID."""
        async with async_session() as session:
            result = await session.execute(
                select(Contact).where(Contact.id == contact_id)
            )
            contact = result.scalar_one_or_none()
            return self._contact_to_dict(contact) if contact else None

    async def get_interactions(self, contact_id: str) -> list[dict]:
        """Get all interactions for a contact."""
        async with async_session() as session:
            result = await session.execute(
                select(Interaction)
                .where(Interaction.contact_id == contact_id)
                .order_by(Interaction.occurred_at.desc())
            )
            interactions = result.scalars().all()
            return [self._interaction_to_dict(i) for i in interactions]

    def _contact_to_dict(self, contact: Contact) -> dict:
        """Convert a Contact model to a dictionary."""
        return {
            "id": contact.id,
            "founder_id": contact.founder_id,
            "name": contact.name,
            "email": contact.email,
            "company": contact.company,
            "role": contact.role,
            "type": contact.type,
            "pipeline_stage": contact.pipeline_stage,
            "notes": contact.notes,
            "last_contacted_at": contact.last_contacted_at.isoformat() if contact.last_contacted_at else None,
            "created_at": contact.created_at.isoformat() if contact.created_at else None,
        }

    def _interaction_to_dict(self, interaction: Interaction) -> dict:
        """Convert an Interaction model to a dictionary."""
        return {
            "id": interaction.id,
            "contact_id": interaction.contact_id,
            "founder_id": interaction.founder_id,
            "type": interaction.type,
            "summary": interaction.summary,
            "details": interaction.details,
            "occurred_at": interaction.occurred_at.isoformat() if interaction.occurred_at else None,
            "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
        }
