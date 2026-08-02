"""Tests for the investor database."""

import pytest

from fundfy.integrations.investor_db import InvestorDatabase


@pytest.fixture
def investor_db():
    """Create an InvestorDatabase instance."""
    return InvestorDatabase()


class TestInvestorDatabase:
    """Tests for investor search and CRUD."""

    async def test_add_investor(self, investor_db):
        """Test adding an investor."""
        result = await investor_db.add({
            "name": "Test Investor",
            "firm": "Test VC",
            "focus_areas": ["SaaS", "AI/ML"],
            "stage_preference": "seed",
            "check_size_min": 100000,
            "check_size_max": 1000000,
            "location": "San Francisco, CA",
        })
        assert result["name"] == "Test Investor"
        assert result["firm"] == "Test VC"
        assert "SaaS" in result["focus_areas"]
        assert result["id"] is not None

    async def test_get_investor(self, investor_db):
        """Test getting an investor by ID."""
        created = await investor_db.add({
            "name": "Get Test",
            "firm": "Get VC",
            "focus_areas": ["Fintech"],
        })
        result = await investor_db.get(created["id"])
        assert result is not None
        assert result["name"] == "Get Test"

    async def test_search_by_stage(self, investor_db):
        """Test searching by stage preference."""
        await investor_db.add({
            "name": "Seed Investor",
            "firm": "Seed Fund",
            "focus_areas": ["SaaS"],
            "stage_preference": "seed",
        })
        await investor_db.add({
            "name": "Series A Investor",
            "firm": "Growth Fund",
            "focus_areas": ["SaaS"],
            "stage_preference": "series-a",
        })

        results = await investor_db.search({"stage": "seed"})
        assert len(results) >= 1
        assert all(r["stage_preference"] == "seed" for r in results)

    async def test_search_by_industry(self, investor_db):
        """Test searching by industry/focus area."""
        await investor_db.add({
            "name": "AI Investor",
            "firm": "AI Capital",
            "focus_areas": ["AI/ML", "Deep Tech"],
            "stage_preference": "seed",
        })
        await investor_db.add({
            "name": "Health Investor",
            "firm": "Health Fund",
            "focus_areas": ["Healthcare", "Biotech"],
            "stage_preference": "seed",
        })

        results = await investor_db.search({"industry": "AI/ML"})
        assert len(results) >= 1
        assert any("AI/ML" in r["focus_areas"] for r in results)

    async def test_search_by_location(self, investor_db):
        """Test searching by location."""
        await investor_db.add({
            "name": "NYC Investor",
            "firm": "NYC Fund",
            "focus_areas": ["Fintech"],
            "location": "New York, NY",
        })

        results = await investor_db.search({"location": "New York"})
        assert len(results) >= 1

    async def test_search_by_check_size(self, investor_db):
        """Test searching by check size range."""
        await investor_db.add({
            "name": "Small Check",
            "firm": "Angel",
            "focus_areas": ["SaaS"],
            "check_size_min": 25000,
            "check_size_max": 100000,
        })
        await investor_db.add({
            "name": "Big Check",
            "firm": "Growth VC",
            "focus_areas": ["SaaS"],
            "check_size_min": 5000000,
            "check_size_max": 25000000,
        })

        results = await investor_db.search({"check_size_min": 1000000})
        assert len(results) >= 1
        assert all(r["check_size_max"] >= 1000000 for r in results)

    async def test_update_investor(self, investor_db):
        """Test updating an investor."""
        created = await investor_db.add({
            "name": "Update Test",
            "firm": "Old Firm",
            "focus_areas": ["SaaS"],
        })
        updated = await investor_db.update(created["id"], {"firm": "New Firm"})
        assert updated is not None
        assert updated["firm"] == "New Firm"

    async def test_seed_from_file(self, investor_db):
        """Test seeding from the JSON file."""
        count = await investor_db.seed_from_file()
        assert count > 0  # Should seed at least some investors

    async def test_get_nonexistent(self, investor_db):
        """Test getting a nonexistent investor."""
        result = await investor_db.get("nonexistent-id")
        assert result is None
