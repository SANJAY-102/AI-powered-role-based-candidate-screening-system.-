from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func

from db import Base


class QAPair(Base):
    """Stores each question-answer pair within an interview session."""

    __tablename__ = "qa_pairs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    score = Column(Integer)  # Confidence score 1-5 from LLM evaluation
    source_chunk = Column(Text)  # Which knowledge base chunk grounded this question
    question_order = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
