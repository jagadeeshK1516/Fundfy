"""Phase C — real-world integrations tables.

Revision ID: 002_phase_c
Revises: 001_initial_schema
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "002_phase_c"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Phase C tables."""
    # OAuth tokens
    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("founder_id", sa.String(), nullable=False, index=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Email approvals
    op.create_table(
        "email_approvals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("founder_id", sa.String(), nullable=False, index=True),
        sa.Column("to", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Investors
    op.create_table(
        "investors",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("firm", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("linkedin_url", sa.String(), nullable=True),
        sa.Column("focus_areas", sa.Text(), server_default="[]"),
        sa.Column("stage_preference", sa.String(), nullable=True),
        sa.Column("check_size_min", sa.Float(), nullable=True),
        sa.Column("check_size_max", sa.Float(), nullable=True),
        sa.Column("portfolio_companies", sa.Text(), server_default="[]"),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Grants
    op.create_table(
        "grants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("amount_min", sa.Float(), nullable=True),
        sa.Column("amount_max", sa.Float(), nullable=True),
        sa.Column("deadline", sa.String(), nullable=True),
        sa.Column("eligibility_criteria", sa.Text(), server_default="[]"),
        sa.Column("industry_focus", sa.Text(), server_default="[]"),
        sa.Column("application_url", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="open"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Grant applications
    op.create_table(
        "grant_applications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("founder_id", sa.String(), nullable=False, index=True),
        sa.Column("grant_id", sa.String(), nullable=False),
        sa.Column("business_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="discovered"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # CRM Contacts
    op.create_table(
        "contacts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("founder_id", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("type", sa.String(), server_default="other"),
        sa.Column("pipeline_stage", sa.String(), server_default="lead"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_contacted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # CRM Interactions
    op.create_table(
        "interactions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("contact_id", sa.String(), nullable=False, index=True),
        sa.Column("founder_id", sa.String(), nullable=False, index=True),
        sa.Column("type", sa.String(), server_default="note"),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("founder_id", sa.String(), nullable=False, index=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data", sa.Text(), server_default="{}"),
        sa.Column("read", sa.Boolean(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop Phase C tables."""
    op.drop_table("notifications")
    op.drop_table("interactions")
    op.drop_table("contacts")
    op.drop_table("grant_applications")
    op.drop_table("grants")
    op.drop_table("investors")
    op.drop_table("email_approvals")
    op.drop_table("oauth_tokens")
