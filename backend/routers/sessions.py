"""
Sessions Router

Handles session creation, resume upload/parsing, and session retrieval.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.session import InterviewSession
from services.resume_parser import parse_resume_pdf

router = APIRouter()


class CreateSessionRequest(BaseModel):
    role: str
    config: dict | None = None


class CreateSessionResponse(BaseModel):
    session_id: str
    role: str
    status: str
    config: dict | None = None


class ResumeParseResponse(BaseModel):
    session_id: str
    skills: list[str]
    technologies: list[str]
    experience_level: str


@router.post("", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest, db: Session = Depends(get_db)):
    """Create a new interview session for the specified role."""
    try:
        config_data = request.config or {"question_count": 5, "personality": "Professional Mentor"}
        session = InterviewSession(
            role=request.role,
            extracted_skills=json.dumps({"config": config_data})
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return CreateSessionResponse(
            session_id=session.id,
            role=session.role,
            status=session.status,
            config=config_data,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/{session_id}/resume", response_model=ResumeParseResponse)
async def upload_resume(
    session_id: str,
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and parse a resume PDF, extracting skills and technologies."""
    # Validate session exists
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate file type
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        # Read file bytes
        file_bytes = await resume.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Parse resume
        parsed = parse_resume_pdf(file_bytes)

        # Retrieve existing config
        existing_config = {"question_count": 5, "personality": "Professional Mentor"}
        if session.extracted_skills:
            try:
                existing_data = json.loads(session.extracted_skills)
                if "config" in existing_data:
                    existing_config = existing_data["config"]
            except Exception:
                pass

        # Update session with parsed data
        session.resume_text = parsed["raw_text"]
        session.extracted_skills = json.dumps({
            "skills": parsed["skills"],
            "technologies": parsed["technologies"],
            "experience_level": parsed["experience_level"],
            "domain": parsed["domain"],
            "config": existing_config,
        })
        db.commit()

        return ResumeParseResponse(
            session_id=session_id,
            skills=parsed["skills"],
            technologies=parsed["technologies"],
            experience_level=parsed["experience_level"],
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")


@router.post("/{session_id}/mock-resume", response_model=ResumeParseResponse)
def mock_resume(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Bypasses PDF upload and assigns predefined top-tier mock skills based on role."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build typical top-tier mock data based on the chosen role
    role_lower = session.role.lower()
    if "ml" in role_lower or "machine" in role_lower:
        mock_data = {
            "skills": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Statistics"],
            "technologies": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "Hugging Face", "Pandas", "NumPy"],
            "experience_level": "senior",
            "domain": "AI/ML Engineering"
        }
    elif "data" in role_lower:
        mock_data = {
            "skills": ["Data Analysis", "Data Science", "A/B Testing", "Feature Engineering", "Data Visualization"],
            "technologies": ["Python", "SQL", "Pandas", "scikit-learn", "Tableau", "Spark"],
            "experience_level": "mid",
            "domain": "Data Science"
        }
    else:  # Backend or other
        mock_data = {
            "skills": ["Backend Development", "System Design", "Database Optimization", "CI/CD", "APIs"],
            "technologies": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "AWS", "Git"],
            "experience_level": "mid",
            "domain": "Backend Software Engineering"
        }

    try:
        # Retrieve existing config
        existing_config = {"question_count": 5, "personality": "Professional Mentor"}
        if session.extracted_skills:
            try:
                existing_data = json.loads(session.extracted_skills)
                if "config" in existing_data:
                    existing_config = existing_data["config"]
            except Exception:
                pass

        session.resume_text = f"Mock profile generated for role: {session.role}. Core Skills: {', '.join(mock_data['skills'])}."
        session.extracted_skills = json.dumps({
            "skills": mock_data["skills"],
            "technologies": mock_data["technologies"],
            "experience_level": mock_data["experience_level"],
            "domain": mock_data["domain"],
            "config": existing_config,
        })
        db.commit()

        return ResumeParseResponse(
            session_id=session_id,
            skills=mock_data["skills"],
            technologies=mock_data["technologies"],
            experience_level=mock_data["experience_level"],
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to mock resume: {str(e)}")


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get full session information."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Parse extracted skills
    skills_data = {}
    if session.extracted_skills:
        try:
            skills_data = json.loads(session.extracted_skills)
        except json.JSONDecodeError:
            skills_data = {"skills": [session.extracted_skills]}

    return {
        "session_id": session.id,
        "role": session.role,
        "status": session.status,
        "resume_uploaded": bool(session.resume_text),
        "extracted_skills": skills_data,
        "created_at": str(session.created_at) if session.created_at else None,
    }
