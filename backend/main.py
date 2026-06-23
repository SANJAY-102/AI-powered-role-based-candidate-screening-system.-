from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import Base, engine
from routers import sessions, interview

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Interview AI",
    description="AI-powered role-based candidate screening system with RAG pipeline",
    version="1.0.0",
)

# CORS: allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(interview.router, prefix="/sessions", tags=["interview"])


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Interview AI"}
