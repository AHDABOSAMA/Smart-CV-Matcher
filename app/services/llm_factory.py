"""
LLM Factory — Factory Design Pattern
──────────────────────────────────────
Provides a single interface for calling different LLM backends.
Adding a new provider = adding one class + one entry in the factory dict.

Supported providers:
  • gemini  — Google Gemini 1.5 Flash (free tier, generous limits)
  • openai  — OpenAI GPT-4o-mini
  • ollama  — Local Ollama (e.g., Mistral, Llama3) — fully offline
"""
from typing import Optional
import logging
from abc import ABC, abstractmethod
from typing import List, Dict

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── Base interface every provider must implement ──────────────────────────────

class BaseLLM(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Send a prompt and return the text response."""


# ── Provider implementations ──────────────────────────────────────────────────

class GeminiLLM(BaseLLM):
    """Google Gemini via REST API — free tier, no SDK needed."""

    MODEL = "gemini-1.5-flash-latest"

    def generate(self, system_prompt: str, user_message: str) -> str:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_message}"}],
                }
            ],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
        }
        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            logger.error(f"Gemini response parse error: {data}")
            raise RuntimeError(f"Failed to parse Gemini response: {e}")


class OpenAILLM(BaseLLM):
    """OpenAI GPT-4o-mini via REST API."""

    MODEL = "gpt-4o-mini"

    def generate(self, system_prompt: str, user_message: str) -> str:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            "temperature": 0.2,
            "max_tokens":  1024,
        }
        with httpx.Client(timeout=600) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]


class OllamaLLM(BaseLLM):

    def generate(self, system_prompt: str, user_message: str) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"

        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "stream": False
        }

        with httpx.Client(timeout=120) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["message"]["content"]


# ── The Factory ───────────────────────────────────────────────────────────────

_PROVIDER_MAP: Dict[str, type] = {
    "gemini": GeminiLLM,
    "openai": OpenAILLM,
    "ollama": OllamaLLM,
}


def get_llm(provider: Optional[str] = None) -> BaseLLM:
    """
    Factory function — returns the correct LLM instance.
    provider overrides the global config for per-request switching.
    """
    key = (provider or settings.LLM_PROVIDER).lower()
    cls = _PROVIDER_MAP.get(key)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider: '{key}'. "
            f"Valid options: {list(_PROVIDER_MAP.keys())}"
        )
    return cls()
