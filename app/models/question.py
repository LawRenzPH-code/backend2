# app/models/question.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import json
from app.db.base import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    level = Column(String, nullable=True)  # Bloom's taxonomy level
    type = Column(String, nullable=True)    # Question type (multiple_choice, fill_in_blanks, etc.)
    options = Column(Text, nullable=True)  # JSON string for options
    context = Column(Text, nullable=True)   # Original context from which the question was generated
    bank_id = Column(Integer, ForeignKey("question_banks.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bank = relationship("QuestionBank", back_populates="questions")
    
    # Helper methods for JSON serialization/deserialization
    @property
    def options_dict(self):
        if self.options:
            try:
                return json.loads(self.options)
            except:
                return {}
        return {}
        
    @options_dict.setter
    def options_dict(self, options_dict):
        if options_dict:
            self.options = json.dumps(options_dict)
        else:
            self.options = None