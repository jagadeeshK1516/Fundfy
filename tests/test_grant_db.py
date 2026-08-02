"""Tests for the grant database."""

import pytest

from fundfy.integrations.grant_db import GrantDatabase


@pytest.fixture
def grant_db():
    """Create a GrantDatabase instance."""
    return GrantDatabase()


class TestGrantDatabase:
    """Tests for grant search and matching."""

    async def test_add_grant(self, grant_db):
        """Test adding a grant."""
        result = await grant_db.add({
            "name": "Test Innovation Grant",
            "provider": "Test Foundation",
            "amount_min": 50000,
            "amount_max": 200000,
            "deadline": "2025-06-01",
            "eligibility_criteria": ["US-based", "Tech startup"],
            "industry_focus": ["Technology", "AI/ML"],
            "application_url": "https://example.com/apply",
            "description": "A test grant for innovation",
            "region": "United States",
            "status": "open",
        })
        assert result["name"] == "Test Innovation Grant"
        assert result["amount_max"] == 200000
        assert result["id"] is not None

    async def test_get_grant(self, grant_db):
        """Test getting a grant by ID."""
        created = await grant_db.add({
            "name": "Get Test Grant",
            "provider": "Get Foundation",
            "amount_min": 10000,
            "amount_max": 50000,
            "industry_focus": ["Healthcare"],
            "region": "Global",
        })
        result = await grant_db.get(created["id"])
        assert result is not None
        assert result["name"] == "Get Test Grant"

    async def test_search_by_industry(self, grant_db):
        """Test searching grants by industry."""
        await grant_db.add({
            "name": "AI Grant",
            "provider": "AI Foundation",
            "industry_focus": ["AI/ML", "Technology"],
            "status": "open",
        })
        await grant_db.add({
            "name": "Health Grant",
            "provider": "Health Foundation",
            "industry_focus": ["Healthcare"],
            "status": "open",
        })

        results = await grant_db.search({"industry": "AI/ML"})
        assert len(results) >= 1
        assert any("AI/ML" in r["industry_focus"] for r in results)

    async def test_search_by_amount(self, grant_db):
        """Test searching grants by amount range."""
        await grant_db.add({
            "name": "Small Grant",
            "provider": "Small Foundation",
            "amount_min": 1000,
            "amount_max": 10000,
            "status": "open",
        })
        await grant_db.add({
            "name": "Big Grant",
            "provider": "Big Foundation",
            "amount_min": 500000,
            "amount_max": 2000000,
            "status": "open",
        })

        results = await grant_db.search({"amount_min": 100000})
        assert len(results) >= 1
        assert all(r["amount_max"] >= 100000 for r in results)

    async def test_search_by_region(self, grant_db):
        """Test searching grants by region."""
        await grant_db.add({
            "name": "US Grant",
            "provider": "US Gov",
            "region": "United States",
            "status": "open",
        })

        results = await grant_db.search({"region": "United States"})
        assert len(results) >= 1

    async def test_create_application(self, grant_db):
        """Test creating a grant application."""
        grant = await grant_db.add({
            "name": "App Test Grant",
            "provider": "Test",
            "status": "open",
        })
        app = await grant_db.create_application(
            founder_id="test-founder-1",
            grant_id=grant["id"],
            business_id="test-biz-1",
            notes="Interested in this grant",
        )
        assert app["status"] == "discovered"
        assert app["grant_id"] == grant["id"]
        assert app["founder_id"] == "test-founder-1"

    async def test_update_application(self, grant_db):
        """Test updating a grant application status."""
        grant = await grant_db.add({
            "name": "Update App Grant",
            "provider": "Test",
        })
        app = await grant_db.create_application(
            founder_id="test-founder-1",
            grant_id=grant["id"],
        )
        updated = await grant_db.update_application(app["id"], {"status": "applying"})
        assert updated is not None
        assert updated["status"] == "applying"

    async def test_list_applications(self, grant_db):
        """Test listing grant applications for a founder."""
        grant1 = await grant_db.add({"name": "Grant 1", "provider": "P1"})
        grant2 = await grant_db.add({"name": "Grant 2", "provider": "P2"})

        await grant_db.create_application(founder_id="test-founder-1", grant_id=grant1["id"])
        await grant_db.create_application(founder_id="test-founder-1", grant_id=grant2["id"])

        apps = await grant_db.list_applications("test-founder-1")
        assert len(apps) == 2

    async def test_seed_from_file(self, grant_db):
        """Test seeding from the JSON file."""
        count = await grant_db.seed_from_file()
        assert count > 0

    async def test_get_nonexistent(self, grant_db):
        """Test getting a nonexistent grant."""
        result = await grant_db.get("nonexistent-id")
        assert result is None
