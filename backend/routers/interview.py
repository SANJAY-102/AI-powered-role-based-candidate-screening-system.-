"""
Interview Router

Handles the interview flow: fetching questions, submitting answers,
completing sessions, and generating summaries.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.session import InterviewSession
from models.question import QAPair
from services.session_service import (
    get_next_question,
    evaluate_answer,
    get_session_summary,
)

router = APIRouter()


class SubmitAnswerRequest(BaseModel):
    question_id: int
    answer: str


class SubmitAnswerResponse(BaseModel):
    saved: bool
    next_available: bool
    score: int | None = None
    feedback: str | None = None


@router.get("/{session_id}/question")
def get_question(session_id: str, db: Session = Depends(get_db)):
    """
    Get the next RAG-generated interview question for this session.
    Returns adaptive questions based on previous Q&A history.
    """
    # Validate session
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Interview session is already completed")

    try:
        result = get_next_question(session_id, db)
        if result is None:
            return {
                "question_id": None,
                "question": None,
                "question_order": None,
                "max_reached": True,
                "message": "Maximum questions reached. Please complete the interview.",
            }
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate question: {str(e)}",
        )


@router.post("/{session_id}/answer", response_model=SubmitAnswerResponse)
def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db),
):
    """Submit an answer to a question and get it scored."""
    # Validate session
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Find the QA pair
    qa_pair = db.query(QAPair).filter(
        QAPair.id == request.question_id,
        QAPair.session_id == session_id,
    ).first()
    if not qa_pair:
        raise HTTPException(status_code=404, detail="Question not found for this session")

    try:
        # Save the answer
        qa_pair.answer = request.answer
        db.commit()

        # Score the answer (bonus feature)
        score_result = evaluate_answer(request.question_id, request.answer, db)

        # Check if more questions are available
        answered_count = (
            db.query(QAPair)
            .filter(QAPair.session_id == session_id, QAPair.answer.isnot(None))
            .count()
        )
        # Retrieve custom max_questions config
        max_q = 5
        if session.extracted_skills:
            try:
                import json
                skill_data = json.loads(session.extracted_skills)
                if isinstance(skill_data, dict) and "config" in skill_data:
                    max_q = int(skill_data["config"].get("question_count", 5))
            except Exception:
                pass
        next_available = answered_count < max_q

        return SubmitAnswerResponse(
            saved=True,
            next_available=next_available,
            score=score_result.get("score"),
            feedback=score_result.get("feedback"),
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save answer: {str(e)}")


@router.post("/{session_id}/complete")
def complete_session(session_id: str, db: Session = Depends(get_db)):
    """Mark an interview session as completed."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        session.status = "completed"
        db.commit()
        return {"session_id": session_id, "status": "completed"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete session: {str(e)}")


@router.get("/{session_id}/summary")
def get_summary(session_id: str, db: Session = Depends(get_db)):
    """
    Get the full interview summary with Q&A pairs, analysis,
    topic coverage, and confidence scores.
    """
    try:
        summary = get_session_summary(session_id, db)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}",
        )
