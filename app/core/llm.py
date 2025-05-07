# app/core/llm.py
import openai
from typing import List, Dict, Any, Optional
import logging
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.warning("No OpenAI API key provided")
            
    def extract_text_from_file(self, file_content: bytes, file_name: str) -> str:
        """Extract text from various file formats (PDF, DOCX, TXT)"""
        import PyPDF2
        import docx
        import io
        
        file_extension = file_name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            # Handle PDF
            pdf_file = io.BytesIO(file_content)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
            
        elif file_extension in ['docx', 'doc']:
            # Handle DOCX
            doc_file = io.BytesIO(file_content)
            doc = docx.Document(doc_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
            
        elif file_extension == 'txt':
            # Handle TXT
            return file_content.decode('utf-8')
            
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
            
    def generate_questions(
        self, 
        text: str, 
        remember: int = 0,
        understand: int = 0,
        apply: int = 0,
        analyze: int = 0,
        evaluate: int = 0,
        create: int = 0,
        multiple_choice: int = 0,
        fill_in_blanks: int = 0,
        true_false: int = 0
    ) -> List[Dict[str, Any]]:
        """Generate questions using OpenAI"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required for question generation")
            
        # Create the prompt for GPT
        bloom_counts = {
            "Remember": remember,
            "Understand": understand,
            "Apply": apply,
            "Analyze": analyze,
            "Evaluate": evaluate,
            "Create": create
        }
        
        question_types = {
            "multiple_choice": multiple_choice,
            "fill_in_blanks": fill_in_blanks,
            "true_false": true_false
        }
        
        # Filter out zero counts
        bloom_counts = {k: v for k, v in bloom_counts.items() if v > 0}
        question_types = {k: v for k, v in question_types.items() if v > 0}
        
        if not bloom_counts or not question_types:
            raise ValueError("At least one Bloom's taxonomy level and one question type must be selected")
        
        prompt = f"""
        Based on the following text, generate assessment questions according to these specifications:
        
        Text: {text[:4000]}... (text truncated for brevity)
        
        Bloom's Taxonomy Levels:
        {', '.join([f"{count} {level}" for level, count in bloom_counts.items()])}
        
        Question Types:
        {', '.join([f"{count} {qtype.replace('_', ' ')}" for qtype, count in question_types.items()])}
        
        For each question, provide:
        1. The question text
        2. The correct answer
        3. The Bloom's taxonomy level
        4. The question type
        5. For multiple-choice questions, provide 4 options including the correct answer
        
        Format the response as a JSON list with this structure:
        [
            {{
                "question": "Question text here",
                "answer": "Correct answer here",
                "level": "Bloom's level (Remember, Understand, etc.)",
                "type": "Question type (multiple_choice, fill_in_blanks, true_false)",
                "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}} (only for multiple_choice)
            }},
            ...
        ]
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # or "gpt-3.5-turbo" depending on your preference
                messages=[
                    {"role": "system", "content": "You are an expert assessment creator specialized in generating questions based on Bloom's Taxonomy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # Parse the response and ensure it's valid JSON
            import json
            try:
                content = response.choices[0].message.content
                questions = json.loads(content)
                return questions
            except json.JSONDecodeError:
                logger.error(f"Failed to parse response as JSON: {content}")
                # Attempt to extract JSON from the response if it contains other text
                import re
                json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                if json_match:
                    try:
                        questions = json.loads(json_match.group(0))
                        return questions
                    except json.JSONDecodeError:
                        pass
                        
                raise ValueError("Failed to parse the AI response as valid JSON")
                
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            raise
            
    def rephrase_question(
        self,
        question_text: str,
        question_type: Optional[str] = None,
        bloom_level: Optional[str] = None
    ) -> Dict[str, str]:
        """Rephrase a question using OpenAI"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required for question rephrasing")
            
        type_info = f" as a {question_type} question" if question_type else ""
        level_info = f" at the {bloom_level} level of Bloom's taxonomy" if bloom_level else ""
        
        prompt = f"""
        Rephrase the following assessment question{type_info}{level_info}. 
        Keep the meaning and difficulty level the same but use different wording:
        
        Original question: {question_text}
        
        Respond with JSON in this format:
        {{
            "original": "original question",
            "rephrased": "rephrased question"
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Using a smaller model for rephrasing
                messages=[
                    {"role": "system", "content": "You are an expert at rephrasing assessment questions while maintaining their educational purpose."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse the response and ensure it's valid JSON
            import json
            try:
                content = response.choices[0].message.content
                result = json.loads(content)
                # Add type and level if provided
                if question_type:
                    result["type"] = question_type
                if bloom_level:
                    result["level"] = bloom_level
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse rephrase response as JSON: {content}")
                # Return a structured response even if JSON parsing fails
                return {
                    "original": question_text,
                    "rephrased": content.strip(),
                    "type": question_type,
                    "level": bloom_level
                }
                
        except Exception as e:
            logger.error(f"Error rephrasing question: {str(e)}")
            raise