from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.schemas import GenerateQuizRequest, GenerateQuizResponse
from app.services.llm_client import generate_quiz_via_llm

router = APIRouter()

@router.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz_endpoint(payload: GenerateQuizRequest):
    try:
        quiz, model = await generate_quiz_via_llm(payload)
        return GenerateQuizResponse(
            quiz=quiz,
            model=model,
            createdAt=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:  # narrow exception types in real code
        raise HTTPException(status_code=502, detail={"code": "LLM_UPSTREAM_ERROR", "message": str(exc)})
