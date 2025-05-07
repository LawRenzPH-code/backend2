# app/crud/crud_question.py
from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionUpdate
import json

class CRUDQuestion(CRUDBase[Question, QuestionCreate, QuestionUpdate]):
    def create(self, db: Session, *, obj_in: QuestionCreate) -> Question:
        obj_in_data = obj_in.dict()
        
        # Convert options to JSON string
        if "options" in obj_in_data and obj_in_data["options"]:
            obj_in_data["options"] = json.dumps(obj_in_data["options"])
            
        db_obj = Question(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
        
    def get_by_bank(self, db: Session, *, bank_id: int, skip: int = 0, limit: int = 100) -> List[Question]:
        return db.query(Question).filter(Question.bank_id == bank_id).offset(skip).limit(limit).all()
    
    def get_by_level(self, db: Session, *, level: str, skip: int = 0, limit: int = 100) -> List[Question]:
        return db.query(Question).filter(Question.level == level).offset(skip).limit(limit).all()
    
    def get_by_type(self, db: Session, *, type: str, skip: int = 0, limit: int = 100) -> List[Question]:
        return db.query(Question).filter(Question.type == type).offset(skip).limit(limit).all()

question_crud = CRUDQuestion(Question)