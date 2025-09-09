from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
import httpx
from app.core.config import get_settings
from app.schemas import GenerateQuizRequest, Quiz, QuizQuestion

settings = get_settings()

SYSTEM_PROMPT = (
    "You generate multiple-choice quizzes. Return strict JSON matching the schema: "
    "{\"topic\": string, \"questions\": [{\"id\": string, \"prompt\": string, \"options\": string[], \"correctIndex\": number, \"explanation\"?: string}]} "
    "Respond with JSON only, no code fences."
)


def build_user_prompt(payload: GenerateQuizRequest) -> str:
    return (
        "Generate a quiz as JSON with fields topic and questions. "
        f"Topic: {payload.topic}. Questions: {payload.numQuestions}. Options per question: {payload.optionsPerQuestion}. "
        f"Difficulty: {payload.difficulty or 'medium'}. Ensure exactly one correct answer per question and valid JSON."
    )


def try_parse_quiz_json(content: str, fallback_topic: str) -> Quiz:
    # Remove code fences if present
    content = content.strip()
    content = re.sub(r"^```(?:json)?\n|\n```$", "", content, flags=re.IGNORECASE)

    # Try direct parse
    try:
        parsed = json.loads(content)
        questions = [QuizQuestion(**q) for q in parsed.get("questions", [])]
        return Quiz(topic=parsed.get("topic", fallback_topic), questions=questions)
    except Exception:
        pass

    # Try extracting first JSON object
    try:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(content[start : end + 1])
            questions = [QuizQuestion(**q) for q in parsed.get("questions", [])]
            return Quiz(topic=parsed.get("topic", fallback_topic), questions=questions)
    except Exception:
        pass

    # Fallback minimal quiz if parsing fails
    return Quiz(
        topic=fallback_topic,
        questions=[
            QuizQuestion(
                id="q1",
                prompt=f"Which statement best relates to {fallback_topic}?",
                options=[f"{fallback_topic} fact 1", f"{fallback_topic} distractor 1.2", f"{fallback_topic} distractor 1.3", f"{fallback_topic} distractor 1.4"],
                correctIndex=0,
                explanation=f"The correct option mentions a core {fallback_topic} idea.",
            )
        ],
    )


async def _post_json(url: str, headers: Dict[str, str], data: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()


def _mock_quiz(payload: GenerateQuizRequest) -> Quiz:
    topic = payload.topic.strip() or "General Knowledge"
    num = payload.numQuestions
    opts = payload.optionsPerQuestion
    questions: List[QuizQuestion] = []
    for i in range(num):
        correct_index = i % opts
        options = [
            f"{topic} fact {i + 1}" if j == correct_index else f"{topic} distractor {i + 1}.{j + 1}"
            for j in range(opts)
        ]
        questions.append(
            QuizQuestion(
                id=f"q{i+1}",
                prompt=f"Question {i+1}: Which statement best relates to {topic}?",
                options=options,
                correctIndex=correct_index,
                explanation=f"The correct option mentions a core {topic} idea.",
            )
        )
    return Quiz(topic=topic, questions=questions)


@retry(stop=stop_after_attempt(2), wait=wait_exponential_jitter(initial=0.5, max=2))
async def generate_quiz_via_llm(payload: GenerateQuizRequest) -> tuple[Quiz, str]:
    if settings.use_mock:
        return _mock_quiz(payload), "mock"

    provider = settings.provider
    user_prompt = build_user_prompt(payload)

    if provider == "groq":
        if not settings.groq_api_key:
            return _mock_quiz(payload), "mock"
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": settings.groq_model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            body = await _post_json(url, headers, data, settings.request_timeout_seconds)
            content = body["choices"][0]["message"]["content"]
            quiz = try_parse_quiz_json(content, payload.topic)
            return quiz, settings.groq_model
        except Exception:
            return _mock_quiz(payload), "mock"

    if provider == "openrouter":
        if not settings.openrouter_api_key:
            return _mock_quiz(payload), "mock"
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "AI Quiz",
        }
        data = {
            "model": settings.openrouter_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            body = await _post_json(url, headers, data, settings.request_timeout_seconds)
            content = body["choices"][0]["message"]["content"]
            quiz = try_parse_quiz_json(content, payload.topic)
            return quiz, settings.openrouter_model
        except Exception:
            return _mock_quiz(payload), "mock"

    if provider == "openai":
        if not settings.openai_api_key:
            return _mock_quiz(payload), "mock"
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": settings.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            body = await _post_json(url, headers, data, settings.request_timeout_seconds)
            content = body["choices"][0]["message"]["content"]
            quiz = try_parse_quiz_json(content, payload.topic)
            return quiz, settings.openai_model
        except Exception:
            return _mock_quiz(payload), "mock"

    # Default fallback
    return _mock_quiz(payload), "mock"
