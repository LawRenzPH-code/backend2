# app/api/examinations.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import random

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.crud.crud_question import question_crud
from app.crud.crud_bank import bank_crud

router = APIRouter()

@router.post("/", response_model=Dict[str, Any])
async def create_examination(
    *,
    exam_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an examination from selected questions"""
    try:
        question_ids = exam_config.get("question_ids", [])
        title = exam_config.get("title", "New Examination")
        bloom_levels = exam_config.get("bloom_levels", {})
        question_types = exam_config.get("question_types", {})
        
        if not question_ids:
            raise HTTPException(status_code=400, detail="No questions selected")
            
        # Validate the total count matches
        total_bloom = sum(bloom_levels.values())
        total_types = sum(question_types.values())
        
        if total_bloom != total_types:
            raise HTTPException(
                status_code=400,
                detail=f"Total questions by Bloom level ({total_bloom}) must match total by question type ({total_types})"
            )
            
        # Get all selected questions
        questions = []
        for q_id in question_ids:
            question = question_crud.get(db=db, id=q_id)
            if question:
                questions.append(question)
                
        if not questions:
            raise HTTPException(status_code=404, detail="No valid questions found")
            
        # Apply filters based on Bloom's taxonomy and question types
        filtered_questions = []
        
        # Group questions by levels and types
        level_groups = {}
        type_groups = {}
        
        for q in questions:
            # Group by level
            level = q.level
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(q)
            
            # Group by type
            qtype = q.type
            if qtype not in type_groups:
                type_groups[qtype] = []
            type_groups[qtype].append(q)
        
        # Select questions based on the Bloom's taxonomy configuration
        selected_questions = []
        
        # For each level, select the requested number of questions
        for level, count in bloom_levels.items():
            level_qs = level_groups.get(level.capitalize(), [])  # Capitalize to match DB format
            
            # If not enough questions of this level, use what we have
            actual_count = min(count, len(level_qs))
            
            # Randomly select questions of this level
            selected = random.sample(level_qs, actual_count) if actual_count > 0 else []
            selected_questions.extend(selected)
            
        # Format questions for the response
        result_questions = []
        for q in selected_questions:
            question_data = {
                "id": q.id,
                "question": q.question,
                "answer": q.answer,
                "level": q.level,
                "type": q.type
            }
            
            # Add options for multiple choice
            if q.options:
                try:
                    import json
                    question_data["options"] = json.loads(q.options)
                except:
                    question_data["options"] = {}
                    
            result_questions.append(question_data)
            
        # Create a response
        return {
            "success": True,
            "examination": {
                "title": title,
                "questions": result_questions,
                "total_questions": len(result_questions)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))