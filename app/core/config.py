import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    # Provider: "openrouter" | "openai" | "groq"
    provider: str = os.getenv("PROVIDER", "openrouter").lower()

    # OpenRouter
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")

    # OpenAI
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Groq
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Behavior
    use_mock: bool = os.getenv("USE_MOCK", "false").lower() in {"1", "true", "yes"}
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


def get_settings() -> Settings:
    return Settings()
