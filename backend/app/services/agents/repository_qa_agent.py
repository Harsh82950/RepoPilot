from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.services.llm.llm_provider import LLMProvider


SYSTEM_PROMPT = """
You are RepoPilot, an AI engineering assistant for software repositories.

You have access to repository search tools.

Your job is to answer repository questions using evidence from the
repository.

Rules:

1. Use the repository search tool when repository evidence is needed.
2. Read the returned code carefully.
3. Never infer an operation from a function name alone.
4. Distinguish carefully between:
   - increment vs decrement
   - create vs update
   - reserve vs release
   - debit vs credit
5. If the search results contain multiple functions, associate each
   operation with the function whose implementation actually contains it.
6. Do not invent files, functions, variables, behavior, or line numbers.
7. If the evidence is insufficient, say so.
8. Give a concise technical answer.
"""


def build_agent_messages(question: str) -> list[Any]:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    return [
        SystemMessage(content=SYSTEM_PROMPT.strip()),
        HumanMessage(content=question.strip()),
    ]


def create_repository_agent(
    llm_provider: LLMProvider,
    tools: list[BaseTool],
):
    """
    Create the repository agent.

    The current implementation keeps the agent provider-independent.
    The LLM provider is responsible for generating the model response.
    """

    if not tools:
        raise ValueError("At least one repository tool is required.")

    def invoke(question: str) -> str:
        messages = build_agent_messages(question)

        tool_descriptions = "\n\n".join(
            f"Tool: {tool.name}\n"
            f"Description: {tool.description}"
            for tool in tools
        )

        prompt = (
            SYSTEM_PROMPT.strip()
            + "\n\nAVAILABLE REPOSITORY TOOLS:\n"
            + tool_descriptions
            + "\n\nUSER QUESTION:\n"
            + question.strip()
            + "\n\n"
            "Decide whether repository search is needed. "
            "If repository evidence is needed, use the available "
            "repository search capability before answering."
        )

        return llm_provider.generate(prompt)

    return invoke