## AI Quiz Backend (FastAPI)

This repository contains the FastAPI backend used by the AI‑Powered Knowledge Quiz to proxy LLM requests and protect API keys.

For complete setup and local run instructions, please refer to the main README in the frontend repo:

- ../ai-quiz/README.md

Quick reference:

- Endpoint: POST /api/generate-quiz
- Env vars: PROVIDER=groq|openrouter|openai, GROQ_API_KEY/OPENROUTER_API_KEY/OPENAI_API_KEY, USE_MOCK=true|false

Note: Do not commit your .env or any secrets.
