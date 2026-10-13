"""Local Ollama client. Only aggregate financial summaries are sent."""

import json
import os
from typing import Any

import requests


OLLAMA_UNAVAILABLE = "AI Assistant is currently unavailable. Start Ollama to enable AI-powered recommendations."


def generate_financial_response(financial_context: dict[str, Any], question: str) -> tuple[str | None, str | None]:
    question = question.strip()
    if not question:
        return None, "Enter a question to get a financial insight."
    if len(question) > 1000:
        return None, "Please keep your question under 1,000 characters."
    context = json.dumps(financial_context, ensure_ascii=True, allow_nan=False)
    prompt = (
        "You are a careful personal finance assistant. Use only the aggregate data in the JSON context below. "
        "Never invent amounts, transactions, dates, or model results. If the information is unavailable, say so. "
        "Offer practical, non-judgmental budgeting insights and make clear that predictions are estimates.\n\n"
        f"Financial context (aggregated; contains no names, email addresses, or transaction descriptions):\n{context}\n\n"
        f"User question: {question}\nAnswer:"
    )
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=90,
        )
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        if not answer:
            return None, OLLAMA_UNAVAILABLE
        return answer, None
    except (requests.RequestException, ValueError, TypeError):
        return None, OLLAMA_UNAVAILABLE
