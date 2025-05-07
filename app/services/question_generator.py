# app/services/question_generator.py
from typing import List, Dict, Any, Optional, BinaryIO
import logging
from fastapi import UploadFile
from app.core.llm import LLMService
from app.crud.crud_question import question_crud
from app.schemas.question import QuestionCreate

logger = logging.getLogger(__name__)

class QuestionGeneratorService:
    def __init__(self):
        self.llm_service = None  # Initialized on demand with API key
        
    def _ensure_llm_service(self, api_key: Optional[str] = None):
        if not self.llm_service or api_key:
            self.llm_service = LLMService(api_key=api_key)
        
    async def process_file_and_generate_questions(
        self,
        file: UploadFile,
        remember: int = 0,
        understand: int = 0,
        apply: int = 0,
        analyze: int = 0,
        evaluate: int = 0,
        create: int = 0,
        multiple_choice: int = 0,
        fill_in_blanks: int = 0,
        true_false: int = 0,
        api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Process a file and generate questions based on its content"""
        try:
            self._ensure_llm_service(api_key)
            
            # Validate file extension
            filename = file.filename
            if not filename:
                raise ValueError("Filename is required")
                
            allowed_extensions = ['pdf', 'docx', 'txt']
            file_extension = filename.split('.')[-1].lower()
            
            if file_extension not in allowed_extensions:
                raise ValueError(f"Unsupported file format: {file_extension}. Supported formats: {', '.join(allowed_extensions)}")
            
            # Read file content
            file_content = await file.read()
            
            # Extract text from file
            text = self.llm_service.extract_text_from_file(file_content, filename)
            
            # Generate questions
            questions = self.llm_service.generate_questions(
                text=text,
                remember=remember,
                understand=understand,
                apply=apply,
                analyze=analyze,
                evaluate=evaluate,
                create=create,
                multiple_choice=multiple_choice,
                fill_in_blanks=fill_in_blanks,
                true_false=true_false
            )
            
            # Add IDs to the questions
            for i, question in enumerate(questions):
                question["id"] = i + 1
                
            return questions
            
        except Exception as e:
            logger.error(f"Error in process_file_and_generate_questions: {str(e)}")
            raise
            
    async def save_questions_to_db(
        self, 
        questions: List[Dict[str, Any]], 
        db_session
    ) -> List[Dict[str, Any]]:
        """Save generated questions to the database"""
        db_questions = []
        
        for q in questions:
            question_create = QuestionCreate(
                question=q["question"],
                answer=q.get("answer"),
                level=q.get("level"),
                type=q.get("type"),
                options=q.get("options"),
                bank_id=q.get("bank_id")
            )
            
            db_question = question_crud.create(db=db_session, obj_in=question_create)
            db_questions.append(db_question)
            
        return db_questions
        
    async def rephrase_question(
        self,
        question_text: str,
        question_type: Optional[str] = None,
        bloom_level: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, str]:
        """Rephrase a question using LLM"""
        self._ensure_llm_service(api_key)
        
        result = self.llm_service.rephrase_question(
            question_text=question_text,
            question_type=question_type,
            bloom_level=bloom_level
        )
        
        return result