import uuid

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from db import Base


class InterviewSession(Base):
    """Represents a single interview session for a candidate."""

    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String, nullable=False)
    resume_text = Column(Text)
    extracted_skills = Column(Text)  # JSON string of parsed skills
    status = Column(String, default="active")  # active | completed
    created_at = Column(DateTime, server_default=func.now())
