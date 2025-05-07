# app/api/question_banks.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.deps import get_db, get_current_user
from app.crud.crud_bank import bank_crud
from app.crud.crud_question import question_crud
from app.models.user import User
from app.schemas.question_bank import (
    QuestionBankCreate,
    QuestionBankUpdate,
    QuestionBankResponse,
    QuestionBankWithQuestions
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[QuestionBankResponse])
def read_banks(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all question banks for the current user"""
    banks = bank_crud.get_multi_by_user(
        db=db, 
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Add question count to each bank
    for bank in banks:
        bank.question_count = len(bank.questions) if bank.questions else 0
        
    return banks

@router.post("/", response_model=QuestionBankResponse)
def create_bank(
    *,
    db: Session = Depends(get_db),
    bank_in: QuestionBankCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new question bank"""
    # Check if bank with same name exists
    existing_bank = bank_crud.get_by_name(db=db, name=bank_in.name)
    if existing_bank and existing_bank.user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail=f"A question bank with the name '{bank_in.name}' already exists"
        )
    
    # Set the user_id to the current user
    bank_in_data = bank_in.dict()
    bank_in_data["user_id"] = current_user.id
    
    bank = bank_crud.create(db=db, obj_in=bank_in_data)
    bank.question_count = 0
    
    return bank

@router.get("/{bank_id}", response_model=QuestionBankWithQuestions)
def read_bank(
    *,
    db: Session = Depends(get_db),
    bank_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get a specific question bank with its questions"""
    bank = bank_crud.get(db=db, id=bank_id)
    
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")
        
    if bank.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    return bank

@router.put("/{bank_id}", response_model=QuestionBankResponse)
def update_bank(
    *,
    db: Session = Depends(get_db),
    bank_id: int,
    bank_in: QuestionBankUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a question bank"""
    bank = bank_crud.get(db=db, id=bank_id)
    
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")
        
    if bank.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    bank = bank_crud.update(db=db, db_obj=bank, obj_in=bank_in)
    return bank

@router.delete("/{bank_id}", response_model=QuestionBankResponse)
def delete_bank(
    *,
    db: Session = Depends(get_db),
    bank_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a question bank"""
    bank = bank_crud.get(db=db, id=bank_id)
    
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")
        
    if bank.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    bank = bank_crud.remove(db=db, id=bank_id)
    return bank

@router.get("/{bank_id}/questions", response_model=List)
def read_bank_questions(
    *,
    db: Session = Depends(get_db),
    bank_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get all questions in a bank"""
    bank = bank_crud.get(db=db, id=bank_id)
    
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")
        
    if bank.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    questions = question_crud.get_by_bank(db=db, bank_id=bank_id, skip=skip, limit=limit)
    
    # Convert options from JSON string to dict
    for q in questions:
        if q.options:
            try:
                q.options_dict = q.options_dict
            except:
                q.options_dict = {}
                
    return questions

@router.post("/{bank_id}/questions", response_model=dict)
def add_questions_to_bank(
    *,
    db: Session = Depends(get_db),
    bank_id: int,
    question_ids: List[int],
    current_user: User = Depends(get_current_user)
):
    """Add questions to a bank"""
    bank = bank_crud.get(db=db, id=bank_id)
    
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")
        
    if bank.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    updated_count = 0
    for q_id in question_ids:
        question = question_crud.get(db=db, id=q_id)
        if question:
            question_crud.update(db=db, db_obj=question, obj_in={"bank_id": bank_id})
            updated_count += 1
            
    return {
        "success": True,
        "message": f"{updated_count} questions added to bank",
        "bank_id": bank_id,
        "bank_name": bank.name
    }

@router.delete("/{bank_id}/questions", response_model=dict)
def remove_questions_from_bank(
    *,
    db: Session = Depends(get_db),
    bank_id: int,
    question_ids: List[int],
    current_user: User = Depends(get_current_user)
):
    """Remove questions from a bank"""
    bank = bank_crud.get(db=db, id=bank_id)
    
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")
        
    if bank.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    updated_count = 0
    for q_id in question_ids:
        question = question_crud.get(db=db, id=q_id)
        if question and question.bank_id == bank_id:
            question_crud.update(db=db, db_obj=question, obj_in={"bank_id": None})
            updated_count += 1
            
    return {
        "success": True,
        "message": f"{updated_count} questions removed from bank",
        "bank_id": bank_id,
        "bank_name": bank.name
    }