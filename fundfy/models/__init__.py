"""SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


from fundfy.models.founder import Founder  # noqa: E402, F401
from fundfy.models.business import Business  # noqa: E402, F401
from fundfy.models.conversation import Conversation, Message  # noqa: E402, F401
from fundfy.models.document import Document  # noqa: E402, F401
from fundfy.models.workstream import WorkstreamTask  # noqa: E402, F401
from fundfy.models.email_draft import EmailDraft  # noqa: E402, F401
from fundfy.models.generated_file import GeneratedFile  # noqa: E402, F401
from fundfy.models.job import BackgroundJob  # noqa: E402, F401
from fundfy.models.oauth_token import OAuthToken  # noqa: E402, F401
from fundfy.models.email_approval import EmailApproval  # noqa: E402, F401
from fundfy.models.investor import Investor  # noqa: E402, F401
from fundfy.models.grant import Grant  # noqa: E402, F401
from fundfy.models.grant_application import GrantApplication  # noqa: E402, F401
from fundfy.models.crm import Contact, Interaction  # noqa: E402, F401
from fundfy.models.notification import Notification  # noqa: E402, F401
