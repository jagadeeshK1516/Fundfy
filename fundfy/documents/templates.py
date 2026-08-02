"""Prompt templates for document generation."""

BUSINESS_PLAN = """Generate a comprehensive business plan with the following sections:
1. Executive Summary
2. Company Description
3. Market Analysis
4. Organization & Management
5. Products/Services
6. Marketing & Sales Strategy
7. Financial Projections
8. Funding Requirements

Business Context: {context}"""

EXECUTIVE_SUMMARY = """Generate a compelling executive summary (1-2 pages) covering:
1. Problem statement
2. Solution overview
3. Target market
4. Business model
5. Competitive advantage
6. Financial highlights
7. Team overview
8. Funding ask

Business Context: {context}"""

PITCH_DECK_OUTLINE = """Generate a pitch deck outline (12-15 slides) with:
1. Title/Hook
2. Problem
3. Solution
4. Market Size (TAM/SAM/SOM)
5. Product/Demo
6. Business Model
7. Traction/Milestones
8. Competition
9. Competitive Advantage
10. Team
11. Financial Projections
12. Ask/Use of Funds
13. Vision/Closing

For each slide, provide the key talking points and suggested visuals.

Business Context: {context}"""

PRD = """Generate a Product Requirements Document (PRD) including:
1. Product Overview
2. Goals & Objectives
3. User Personas
4. User Stories & Use Cases
5. Functional Requirements
6. Non-functional Requirements
7. Technical Architecture (high level)
8. Success Metrics
9. Timeline & Milestones
10. Open Questions & Risks

Business Context: {context}"""

BRD = """Generate a Business Requirements Document (BRD) including:
1. Project Overview
2. Business Objectives
3. Stakeholders
4. Current State Analysis
5. Future State Description
6. Scope (In/Out)
7. Business Requirements
8. Constraints & Assumptions
9. Success Criteria
10. Budget & Resource Estimates

Business Context: {context}"""

SOP = """Generate a Standard Operating Procedure document including:
1. Purpose & Scope
2. Roles & Responsibilities
3. Prerequisites
4. Step-by-Step Procedures
5. Quality Control Checks
6. Exception Handling
7. Documentation Requirements
8. Review & Update Schedule

Business Context: {context}"""

FINANCIAL_MODEL = """Generate a financial model outline including:
1. Revenue Model & Assumptions
2. Cost Structure (Fixed & Variable)
3. Unit Economics (CAC, LTV, Margins)
4. 3-Year P&L Projection
5. Cash Flow Statement
6. Break-even Analysis
7. Sensitivity Analysis
8. Key Metrics Dashboard

Business Context: {context}"""

DPR = """Generate a Daily Progress Report template including:
1. Date & Sprint/Phase
2. Completed Tasks
3. In Progress
4. Blocked Items
5. Key Decisions Made
6. Metrics/KPIs Update
7. Tomorrow's Priorities
8. Notes/Comments

Business Context: {context}"""

COMPANY_PROFILE = """Generate a company profile document including:
1. Company Overview
2. Mission & Vision
3. Core Values
4. Products/Services
5. Target Market
6. Competitive Advantages
7. Leadership Team
8. Company History/Timeline
9. Key Achievements
10. Contact Information

Business Context: {context}"""

DOCUMENT_TEMPLATES = {
    "business_plan": BUSINESS_PLAN,
    "executive_summary": EXECUTIVE_SUMMARY,
    "pitch_deck": PITCH_DECK_OUTLINE,
    "prd": PRD,
    "brd": BRD,
    "sop": SOP,
    "financial_model": FINANCIAL_MODEL,
    "dpr": DPR,
    "company_profile": COMPANY_PROFILE,
}
