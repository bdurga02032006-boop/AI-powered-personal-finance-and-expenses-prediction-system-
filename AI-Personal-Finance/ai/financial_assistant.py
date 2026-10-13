"""Local Ollama client. Only aggregate financial summaries are sent."""

import json
import ipaddress
import os
from typing import Any
from urllib.parse import urlsplit

import requests


OLLAMA_UNAVAILABLE = "AI Assistant is currently unavailable. Start Ollama to enable AI-powered recommendations."
LOCAL_ONLY_MESSAGE = "AI Assistant only connects to local Ollama. Set OLLAMA_BASE_URL to a loopback address such as http://localhost:11434."


def _is_loopback_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        if (parsed.scheme not in {"http", "https"} or not hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
            return False
        try:
            return ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            return hostname.lower() == "localhost"
    except ValueError:
        return False


def generate_financial_response(financial_context: dict[str, Any], question: str) -> tuple[str | None, str | None]:
    question = question.strip()
    if not question:
        return None, "Enter a question to get a financial insight."
    if len(question) > 1000:
        return None, "Please keep your question under 1,000 characters."
    context = json.dumps(financial_context, ensure_ascii=True, allow_nan=False)
    prompt = (
        "You are a careful personal finance assistant. Use only the aggregate data in the JSON context below. "
        "Never invent amounts, transactions, dates, or model results. If information is unavailable, say so. "
        "Offer practical, non-judgmental budgeting insights and make clear predictions are estimates.\n\n"
        "Financial context (aggregated; no names, email addresses, or transaction descriptions):\n"
        f"{context}\n\nUser question: {question}\nAnswer:"
    )
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    if not _is_loopback_url(base_url):
        return None, LOCAL_ONLY_MESSAGE
    model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    try:
        response = requests.post(f"{base_url}/api/generate", json={"model": model, "prompt": prompt, "stream": False}, timeout=90)
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        return (answer, None) if answer else (None, OLLAMA_UNAVAILABLE)
    except (requests.RequestException, ValueError, TypeError):
        return None, OLLAMA_UNAVAILABLE
