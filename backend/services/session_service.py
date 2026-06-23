"""
Session Service

Orchestrates the full RAG flow for generating adaptive interview questions:
  1. Load session from DB
  2. Build retrieval query from skills + role
  3. Retrieve relevant knowledge chunks
  4. Generate question grounded in chunks + previous Q&A
  5. Save question to DB and return it
"""

import json
import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from models.session import InterviewSession
from models.question import QAPair
from rag.retriever import retrieve
from rag.generator import generate_questions, score_answer

load_dotenv()

MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS_PER_SESSION", "5"))


def build_rag_query(skills: list[str], role: str) -> str:
    """Combine skills and role into an effective retrieval query."""
    skills_text = ", ".join(skills[:10])  # Limit to top 10 skills
    return f"{role} technical interview covering: {skills_text}"


def get_next_question(session_id: str, db: Session) -> dict | None:
    """
    Generate the next adaptive interview question for a session.

    Returns:
        Dict with question_id, question, question_order, source_chunk.
        None if max questions reached or session not found.
    """
    # 1. Load session
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    if session.status == "completed":
        return None

    # Retrieve config-based question limit
    max_questions = MAX_QUESTIONS
    if session.extracted_skills:
        try:
            skill_data = json.loads(session.extracted_skills)
            if isinstance(skill_data, dict) and "config" in skill_data:
                max_questions = int(skill_data["config"].get("question_count", MAX_QUESTIONS))
        except Exception:
            pass

    # 2. Load previous Q&A pairs
    existing_qa = (
        db.query(QAPair)
        .filter(QAPair.session_id == session_id)
        .order_by(QAPair.question_order)
        .all()
    )

    # Check if we've reached max questions
    current_order = len(existing_qa) + 1
    if current_order > max_questions:
        return None

    # 3. Parse skills from session
    skills = []
    if session.extracted_skills:
        try:
            skill_data = json.loads(session.extracted_skills)
            if isinstance(skill_data, dict):
                skills = skill_data.get("skills", []) + skill_data.get("technologies", [])
            elif isinstance(skill_data, list):
                skills = skill_data
        except json.JSONDecodeError:
            skills = [session.extracted_skills]

    if not skills:
        skills = ["general technical knowledge"]

    # Parse experience level
    experience_level = "mid"
    if session.extracted_skills:
        try:
            skill_data = json.loads(session.extracted_skills)
            if isinstance(skill_data, dict):
                experience_level = skill_data.get("experience_level", "mid")
        except json.JSONDecodeError:
            pass

    # 4. Build query and retrieve chunks
    query = build_rag_query(skills, session.role)
    try:
        retrieved_chunks = retrieve(query, top_k=5)
    except FileNotFoundError as e:
        # FAISS index not built yet — return a graceful error question
        return {
            "question_id": -1,
            "question": "Knowledge base index not found. Please run the FAISS embedder first.",
            "question_order": current_order,
            "source_chunk": str(e),
        }

    # 5. Build previous Q&A for adaptive questioning
    previous_qa = []
    for qa in existing_qa:
        previous_qa.append({
            "question": qa.question,
            "answer": qa.answer or "No answer provided",
        })

    # Retrieve personality config
    personality = "Professional Mentor"
    if session.extracted_skills:
        try:
            skill_data = json.loads(session.extracted_skills)
            if isinstance(skill_data, dict) and "config" in skill_data:
                personality = skill_data["config"].get("personality", "Professional Mentor")
        except Exception:
            pass

    # 6. Generate question
    questions = generate_questions(
        skills=skills,
        role=session.role,
        retrieved_chunks=retrieved_chunks,
        previous_qa=previous_qa if previous_qa else None,
        count=1,
        experience_level=experience_level,
        personality=personality,
    )

    if not questions:
        return None

    generated = questions[0]

    # 7. Save to DB
    qa_pair = QAPair(
        session_id=session_id,
        question=generated["question"],
        source_chunk=generated.get("source_chunk", ""),
        question_order=current_order,
    )
    db.add(qa_pair)
    db.commit()
    db.refresh(qa_pair)

    return {
        "question_id": qa_pair.id,
        "question": qa_pair.question,
        "question_order": qa_pair.question_order,
        "source_chunk": qa_pair.source_chunk,
    }


def evaluate_answer(question_id: int, answer: str, db: Session) -> dict:
    """
    Score a candidate's answer using the LLM.

    Returns:
        Dict with score (1-5) and feedback.
    """
    qa_pair = db.query(QAPair).filter(QAPair.id == question_id).first()
    if not qa_pair:
        return {"score": 0, "feedback": "Question not found"}

    # Get session for role context
    session = db.query(InterviewSession).filter(
        InterviewSession.id == qa_pair.session_id
    ).first()
    role = session.role if session else "Software Engineer"

    result = score_answer(
        question=qa_pair.question,
        answer=answer,
        source_chunk=qa_pair.source_chunk or "",
        role=role,
    )

    # Save score to DB
    qa_pair.score = result["score"]
    db.commit()

    return result


def get_session_summary(session_id: str, db: Session) -> dict:
    """
    Generate a comprehensive interview summary with analysis.

    Returns:
        Full summary dict with session info, Q&A pairs, and analysis.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    qa_pairs = (
        db.query(QAPair)
        .filter(QAPair.session_id == session_id)
        .order_by(QAPair.question_order)
        .all()
    )

    # Parse skills
    skills = []
    if session.extracted_skills:
        try:
            skill_data = json.loads(session.extracted_skills)
            if isinstance(skill_data, dict):
                skills = skill_data.get("skills", [])
            elif isinstance(skill_data, list):
                skills = skill_data
        except json.JSONDecodeError:
            skills = []

    # Build Q&A list
    qa_list = []
    total_answer_length = 0
    answered_count = 0
    for qa in qa_pairs:
        qa_dict = {
            "question_id": qa.id,
            "question": qa.question,
            "answer": qa.answer or "",
            "source_chunk": qa.source_chunk or "",
            "question_order": qa.question_order,
            "score": qa.score,
        }
        qa_list.append(qa_dict)
        if qa.answer:
            total_answer_length += len(qa.answer.split())
            answered_count += 1

    avg_answer_length = (
        total_answer_length // answered_count if answered_count > 0 else 0
    )

    # Topic coverage analysis
    ml_topics = {
        "Classification": ["classification", "classifier", "logistic", "decision tree", "random forest", "svm", "naive bayes"],
        "Regression": ["regression", "linear regression", "polynomial", "ridge", "lasso"],
        "Neural Networks": ["neural network", "deep learning", "cnn", "rnn", "lstm", "transformer", "attention", "backpropagation"],
        "NLP": ["nlp", "natural language", "text", "tokenization", "embedding", "word2vec", "bert", "gpt"],
        "Computer Vision": ["computer vision", "image", "convolutional", "object detection", "segmentation"],
        "Optimization": ["optimization", "gradient descent", "sgd", "adam", "learning rate", "loss function"],
        "Data Processing": ["data preprocessing", "feature engineering", "normalization", "standardization", "pca", "dimensionality"],
        "Model Evaluation": ["accuracy", "precision", "recall", "f1", "auc", "roc", "cross-validation", "overfitting", "underfitting"],
        "Reinforcement Learning": ["reinforcement learning", "reward", "policy", "q-learning", "mdp"],
        "Generative Models": ["gan", "generative", "variational", "autoencoder", "diffusion"],
    }

    topics_covered = []
    all_question_text = " ".join(qa.question.lower() for qa in qa_pairs)
    for topic, keywords in ml_topics.items():
        if any(kw in all_question_text for kw in keywords):
            topics_covered.append(topic)

    # Average score
    scores = [qa.score for qa in qa_pairs if qa.score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # Retrieve config
    config_data = {"question_count": MAX_QUESTIONS, "personality": "Professional Mentor"}
    if session.extracted_skills:
        try:
            skill_data = json.loads(session.extracted_skills)
            if isinstance(skill_data, dict) and "config" in skill_data:
                config_data = skill_data["config"]
        except Exception:
            pass

    return {
        "session_id": session.id,
        "role": session.role,
        "skills": skills,
        "status": session.status,
        "total_questions": len(qa_pairs),
        "qa_pairs": qa_list,
        "config": config_data,
        "analysis": {
            "topics_covered": topics_covered,
            "avg_answer_length": avg_answer_length,
            "avg_score": avg_score,
            "completion_status": session.status,
            "answered_questions": answered_count,
        },
    }
