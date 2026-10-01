import httpx

from app.services.llm.llm_provider import LLMProvider


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:1.5b"
DEFAULT_TIMEOUT = 120.0


class OllamaProvider(LLMProvider):
    """
    LLM provider that communicates with a local Ollama server.
    """

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        ollama_url: str = OLLAMA_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = httpx.post(
                self.ollama_url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Failed to communicate with Ollama: {exc}"
            ) from exc

        data = response.json()

        answer = data.get("response")

        if not answer:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return answer.strip()