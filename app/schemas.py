from pydantic import BaseModel, Field
from typing import List, Optional

class GenerateQuizRequest(BaseModel):
    topic: str
    numQuestions: int = Field(default=5, ge=1, le=20)
    optionsPerQuestion: int = Field(default=4, ge=2, le=6)
    difficulty: Optional[str] = None

class QuizQuestion(BaseModel):
    id: str
    prompt: str
    options: List[str]
    correctIndex: int
    explanation: Optional[str] = None

class Quiz(BaseModel):
    topic: str
    questions: List[QuizQuestion]

class GenerateQuizResponse(BaseModel):
    quiz: Quiz
    model: str
    createdAt: str
