# app/api/questions.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.api.deps import get_db, get_current_user
from app.services.question_generator import QuestionGeneratorService
from app.schemas.question import QuestionResponse, QuestionCreate, QuestionRephrase, RephraseResponse
from app.crud.crud_question import question_crud
from app.crud.crud_bank import bank_crud
from app.models.user import User

router = APIRouter(prefix="/questions")

question_service = QuestionGeneratorService()

@router.get("/test", response_model=dict)
async def test_connection():
    """Test endpoint to verify API is working"""
    return {"status": "success", "message": "API is working"}

@router.post("/generate", response_model=List[dict])
async def generate_questions(
    file: UploadFile = File(...),
    remember: int = Form(0),
    understand: int = Form(0),
    apply: int = Form(0),
    analyze: int = Form(0),
    evaluate: int = Form(0),
    create: int = Form(0),
    multiple_choice: int = Form(0),
    fill_in_blanks: int = Form(0),
    true_false: int = Form(0),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate questions from a file using LLM"""
    try:
        # Validate at least one question type and taxonomy level is selected
        total_questions = remember + understand + apply + analyze + evaluate + create
        total_types = multiple_choice + fill_in_blanks + true_false
        
        if total_questions == 0:
            raise HTTPException(status_code=400, detail="Select at least one Bloom's taxonomy level")
            
        if total_types == 0:
            raise HTTPException(status_code=400, detail="Select at least one question type")
            
        if total_questions != total_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Total question count ({total_questions}) does not match total question types ({total_types})"
            )
        
        # Process file and generate questions
        questions = await question_service.process_file_and_generate_questions(
            file=file,
            remember=remember,
            understand=understand,
            apply=apply,
            analyze=analyze,
            evaluate=evaluate,
            create=create,
            multiple_choice=multiple_choice,
            fill_in_blanks=fill_in_blanks,
            true_false=true_false,
            api_key=api_key
        )
        
        # Save questions to database in background
        db_questions = await question_service.save_questions_to_db(questions, db)
        
        # Update the questions with database IDs
        for i, q in enumerate(questions):
            if i < len(db_questions):
                q["id"] = db_questions[i].id
                
        return questions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rephrase", response_model=RephraseResponse)
async def rephrase_question(
    rephrase_data: QuestionRephrase,
    api_key: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Rephrase a question using LLM"""
    try:
        result = await question_service.rephrase_question(
            question_text=rephrase_data.question_text,
            question_type=rephrase_data.question_type,
            bloom_level=rephrase_data.bloom_level,
            api_key=api_key
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save-to-bank", response_model=dict)
async def save_questions_to_bank(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save questions to a question bank"""
    try:
        question_ids = request.get("question_ids", [])
        bank_id = request.get("bank_id")
        bank_name = request.get("bank_name")
        
        if not question_ids:
            raise HTTPException(status_code=400, detail="No question IDs provided")
            
        # Create bank if needed
        if not bank_id and bank_name:
            bank = bank_crud.create(
                db=db, 
                obj_in={"name": bank_name, "user_id": current_user.id}
            )
            bank_id = bank.id
            
        if not bank_id:
            raise HTTPException(status_code=400, detail="Either bank_id or bank_name must be provided")
            
        # Verify bank exists and user has access
        bank = bank_crud.get(db=db, id=bank_id)
        if not bank:
            raise HTTPException(status_code=404, detail=f"Question bank with ID {bank_id} not found")
            
        if bank.user_id and bank.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have access to this question bank")
            
        # Update questions with bank_id
        updated_count = 0
        for q_id in question_ids:
            question = question_crud.get(db=db, id=q_id)
            if question:
                question_crud.update(db=db, db_obj=question, obj_in={"bank_id": bank_id})
                updated_count += 1
                
        return {
            "success": True,
            "message": f"{updated_count} questions saved to bank",
            "bank_id": bank_id,
            "bank_name": bank.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))