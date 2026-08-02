"""Tests for the CRM service."""

import pytest

from fundfy.integrations.crm import CRMService


@pytest.fixture
def crm_service():
    """Create a CRM service instance."""
    return CRMService()


class TestCRMService:
    """Tests for CRM CRUD operations."""

    async def test_add_contact(self, crm_service):
        """Test adding a contact."""
        result = await crm_service.add_contact(
            "test-founder-1",
            {
                "name": "John Doe",
                "email": "john@example.com",
                "company": "Acme Corp",
                "role": "CEO",
                "type": "investor",
            },
        )
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["type"] == "investor"
        assert result["pipeline_stage"] == "lead"
        assert result["id"] is not None

    async def test_update_contact(self, crm_service):
        """Test updating a contact."""
        contact = await crm_service.add_contact(
            "test-founder-1",
            {"name": "Jane Smith", "type": "mentor"},
        )
        updated = await crm_service.update_contact(
            contact["id"], {"pipeline_stage": "contacted", "notes": "Had intro call"}
        )
        assert updated["pipeline_stage"] == "contacted"
        assert updated["notes"] == "Had intro call"

    async def test_move_stage(self, crm_service):
        """Test moving a contact to a different stage."""
        contact = await crm_service.add_contact(
            "test-founder-1",
            {"name": "Bob Johnson", "type": "investor"},
        )
        result = await crm_service.move_stage(contact["id"], "meeting")
        assert result["pipeline_stage"] == "meeting"

    async def test_log_interaction(self, crm_service):
        """Test logging an interaction."""
        contact = await crm_service.add_contact(
            "test-founder-1",
            {"name": "Alice Williams"},
        )
        interaction = await crm_service.log_interaction(
            contact_id=contact["id"],
            founder_id="test-founder-1",
            data={
                "type": "email",
                "summary": "Sent intro email",
                "details": "Discussed potential partnership",
            },
        )
        assert interaction["type"] == "email"
        assert interaction["summary"] == "Sent intro email"

    async def test_get_pipeline_summary(self, crm_service):
        """Test getting pipeline summary."""
        await crm_service.add_contact(
            "test-founder-1",
            {"name": "Contact A", "pipeline_stage": "lead"},
        )
        await crm_service.add_contact(
            "test-founder-1",
            {"name": "Contact B", "pipeline_stage": "lead"},
        )
        await crm_service.add_contact(
            "test-founder-1",
            {"name": "Contact C", "pipeline_stage": "meeting"},
        )

        summary = await crm_service.get_pipeline_summary("test-founder-1")
        assert summary["lead"] == 2
        assert summary["meeting"] == 1
        assert summary["closed_won"] == 0

    async def test_search_contacts(self, crm_service):
        """Test searching contacts."""
        await crm_service.add_contact(
            "test-founder-1",
            {"name": "Investor Alpha", "type": "investor", "company": "VC Fund"},
        )
        await crm_service.add_contact(
            "test-founder-1",
            {"name": "Mentor Beta", "type": "mentor"},
        )

        # Filter by type
        results = await crm_service.search_contacts(
            "test-founder-1", {"type": "investor"}
        )
        assert len(results) == 1
        assert results[0]["name"] == "Investor Alpha"

    async def test_get_interactions(self, crm_service):
        """Test getting interactions for a contact."""
        contact = await crm_service.add_contact(
            "test-founder-1",
            {"name": "Test Contact"},
        )
        await crm_service.log_interaction(
            contact["id"], "test-founder-1",
            {"type": "call", "summary": "Intro call"},
        )
        await crm_service.log_interaction(
            contact["id"], "test-founder-1",
            {"type": "meeting", "summary": "Follow-up meeting"},
        )

        interactions = await crm_service.get_interactions(contact["id"])
        assert len(interactions) == 2

    async def test_update_nonexistent_contact(self, crm_service):
        """Test updating a contact that doesn't exist."""
        result = await crm_service.update_contact("nonexistent-id", {"name": "New"})
        assert result is None
