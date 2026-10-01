
from app.services.llm.llm_provider import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock LLM used to test RepoPilot's RAG pipeline.

    It does not call an external API. Instead, it demonstrates that
    repository context can be transformed into a grounded answer.
    """

    def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if "wallet balance" in prompt.lower():
            return (
                "The wallet balance is updated in "
                "`src/modules/wallet/wallet.repository.ts`.\n\n"
                "The retrieved repository context shows wallet balance "
                "operations in the following ranges:\n"
                "- Lines 141-220: balance increment/update logic.\n"
                "- Lines 71-150: balance decrement/update logic.\n\n"
                "These operations use the wallet repository to modify "
                "the wallet balance."
            )

        return (
            "The provided repository context was received successfully, "
            "but this mock provider does not have a predefined answer "
            "for the requested question."
        )