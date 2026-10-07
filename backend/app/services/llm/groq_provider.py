import httpx
from typing import Any

from app.core.config import settings
from app.services.llm.llm_provider import LLMProvider


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_TIMEOUT = 120.0

# Keep completion size controlled to avoid unnecessary token usage.
DEFAULT_MAX_COMPLETION_TOKENS = 1200


class GroqProvider(LLMProvider):

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = DEFAULT_MODEL,
        json_mode: bool = True,
        max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
        reasoning_effort: str | None = "low",
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model_name = model_name
        self.json_mode = json_mode
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        if self.max_completion_tokens <= 0:
            raise ValueError(
                "max_completion_tokens must be greater than 0."
            )

    def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.1,
            "max_completion_tokens": self.max_completion_tokens,
        }

        # GPT-OSS supports configurable reasoning effort.
        # Low reasoning is sufficient for our structured
        # repository diagnosis because the repository evidence
        # has already been retrieved and compressed.
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort

        if self.json_mode:
            payload["response_format"] = {
                "type": "json_object",
            }

            payload["reasoning_format"] = "hidden"

        response = self._request(payload)

        choices = response.get("choices", [])

        if not choices:
            raise RuntimeError(
                "Groq returned no choices."
            )

        message = choices[0].get(
            "message",
            {},
        )

        content = message.get("content")

        if not content:
            raise RuntimeError(
                "Groq returned an empty response."
            )

        return content.strip()

    def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if not messages:
            raise ValueError(
                "Messages cannot be empty."
            )

        if not tools:
            raise ValueError(
                "Tools cannot be empty."
            )

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.1,
            "max_completion_tokens": self.max_completion_tokens,
        }

        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort

        response = self._request(payload)

        choices = response.get("choices", [])

        if not choices:
            raise RuntimeError(
                "Groq returned no choices."
            )

        message = choices[0].get(
            "message",
            {},
        )

        return {
            "content": message.get("content"),
            "tool_calls": message.get(
                "tool_calls",
                [],
            ),
        }

    def _request(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                GROQ_URL,
                headers=headers,
                json=payload,
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code >= 400:
                raise RuntimeError(
                    f"Groq API error {response.status_code}: "
                    f"{response.text}"
                )

            return response.json()

        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Failed to communicate with Groq: {exc}"
            ) from exc