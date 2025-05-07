# app/crud/crud_bank.py
from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.question_bank import QuestionBank
from app.schemas.question_bank import QuestionBankCreate, QuestionBankUpdate

class CRUDQuestionBank(CRUDBase[QuestionBank, QuestionBankCreate, QuestionBankUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[QuestionBank]:
        return db.query(QuestionBank).filter(QuestionBank.name == name).first()
        
    def get_multi_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[QuestionBank]:
        return db.query(QuestionBank).filter(QuestionBank.user_id == user_id).offset(skip).limit(limit).all()

bank_crud = CRUDQuestionBank(QuestionBank)