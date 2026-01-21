"""OpenRouter API client wrapper."""

import logging
from typing import Optional

import httpx

from app.config import Config

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Async client for OpenRouter API."""

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        """Initialize the client."""
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def embed(self, text: str, model: Optional[str] = None) -> list[float]:
        """Get embeddings for text."""
        model = model or Config.OR_EMBED_MODEL

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={"input": text, "model": model},
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/crypto-exchange-bot",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Call LLM with message history."""
        model = model or Config.OR_CHAT_MODEL

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/crypto-exchange-bot",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


def get_openrouter_client() -> OpenRouterClient:
    """Get configured OpenRouter client."""
    return OpenRouterClient(
        api_key=Config.OPENROUTER_API_KEY,
        base_url=Config.OPENROUTER_BASE_URL,
    )
