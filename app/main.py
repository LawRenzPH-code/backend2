# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
import logging

from app.api import auth, questions, question_banks, examinations
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created or already exist")
except OperationalError as e:
    logger.error(f"Database error: {e}")
    logger.warning("Continuing without database initialization - some features may not work")

app = FastAPI(
    title="MARIS API",
    description="API for MARIS - Assessment Question Generator",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(questions.router, prefix="/api/v1", tags=["questions"])
app.include_router(question_banks.router, prefix="/api/v1/question-banks", tags=["question-banks"])
app.include_router(examinations.router, prefix="/api/v1/examinations", tags=["examinations"])

@app.get("/")
async def root():
    return {"message": "Welcome to MARIS API"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}