"""Pydantic schemas for structured tool I/O and extraction."""

from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """Standard result container for all tool executions."""

    success: bool
    data: Any = None
    error: str | None = None


class CompetitorProfile(BaseModel):
    """Structured competitor information."""

    name: str
    description: str | None = None
    website: str | None = None
    strengths: list[str] = []
    weaknesses: list[str] = []


class MarketData(BaseModel):
    """Structured market research data."""

    market_size: str | None = None
    growth_rate: str | None = None
    key_trends: list[str] = []
    segments: list[str] = []


class InvestorProfile(BaseModel):
    """Structured investor information."""

    name: str
    firm: str | None = None
    focus_areas: list[str] = []
    stage_preference: str | None = None
    typical_check_size: str | None = None
    website: str | None = None


class GrantOpportunity(BaseModel):
    """Structured grant opportunity information."""

    name: str
    organization: str | None = None
    amount: str | None = None
    deadline: str | None = None
    eligibility: str | None = None
    url: str | None = None
    description: str | None = None
