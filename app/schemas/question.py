# app/schemas/question_bank.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.schemas.question import QuestionResponse

class QuestionBankBase(BaseModel):
    name: str
    description: Optional[str] = None

class QuestionBankCreate(QuestionBankBase):
    user_id: Optional[int] = None

class QuestionBankUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class QuestionBankResponse(QuestionBankBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    question_count: Optional[int] = 0
    
    class Config:
        orm_mode = True

class QuestionBankWithQuestions(QuestionBankResponse):
    questions: List[QuestionResponse] = []