# app/schemas/question.py
from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel

class QuestionBase(BaseModel):
    question: str
    answer: Optional[str] = None
    level: Optional[str] = None
    type: Optional[str] = None
    context: Optional[str] = None
    
class QuestionCreate(QuestionBase):
    options: Optional[Dict[str, str]] = None
    bank_id: Optional[int] = None

class QuestionUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    level: Optional[str] = None
    type: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    bank_id: Optional[int] = None

class QuestionResponse(QuestionBase):
    id: int
    options: Optional[Dict[str, str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class QuestionGenRequest(BaseModel):
    remember: int = 0
    understand: int = 0
    apply: int = 0
    analyze: int = 0
    evaluate: int = 0
    create: int = 0
    multiple_choice: int = 0
    fill_in_blanks: int = 0
    true_false: int = 0
    api_key: Optional[str] = None

class QuestionRephrase(BaseModel):
    question_text: str
    question_type: Optional[str] = None
    bloom_level: Optional[str] = None
    category: Optional[str] = None

class RephraseResponse(BaseModel):
    original: str
    rephrased: str
    type: Optional[str] = None
    level: Optional[str] = None
    category: Optional[str] = None