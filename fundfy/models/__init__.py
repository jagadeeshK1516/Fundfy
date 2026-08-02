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
