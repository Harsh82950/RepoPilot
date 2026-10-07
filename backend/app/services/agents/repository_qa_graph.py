import json
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.services.agents.repository_qa_state import RepositoryQAState
from app.services.agents.repository_tools import create_search_repository_tool
from app.services.embeddings.embedding_provider import EmbeddingProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.llm_provider import LLMProvider


MAX_TOOL_CALLS = 2


SYSTEM_PROMPT = """You are RepoPilot, an AI engineering assistant that answers questions
about software repositories.

You have access to a repository search tool.

Rules:

1. Use repository search when repository evidence is needed.

2. Read the returned code carefully before answering.

3. Never infer an operation from a function name alone.

4. Carefully distinguish:
   - increment vs decrement
   - create vs update
   - reserve vs release
   - debit vs credit

5. When multiple functions are returned, associate each operation with
   the function whose implementation actually contains it.

6. Do not invent files, functions, variables, behavior, or line numbers.

7. If the evidence is insufficient, say so.

8. When search results reveal a function or method call that likely contains
   the requested behavior, search for that exact function or method name
   to locate its implementation.

9. When the user asks where an operation is implemented, do not stop at
   a caller or service layer. Locate the code statement that actually
   performs the operation whenever possible.

10. Prefer exact function names, symbols, or file paths discovered in
    previous search results for follow-up searches instead of broad
    conceptual queries.

11. Do not claim something is the only occurrence unless the evidence
    establishes that.

12. Give a concise technical answer.
"""


def _build_tool_definition() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "search_repository",
            "description": (
                "Search the repository for relevant files, functions, "
                "symbols, and code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The repository search query. Use code symbols, "
                            "function names, file names, or concepts."
                        ),
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    }


def _build_initial_messages(question: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": question,
        },
    ]


def _execute_tool_call(tool, tool_call):
    function_data = tool_call.get("function", {})
    tool_name = function_data.get("name")
    arguments = function_data.get("arguments", "{}")
    tool_call_id = tool_call.get("id")

    if tool_name != tool.name:
        raise ValueError(f"Unknown tool requested: {tool_name}")

    if isinstance(arguments, str):
        arguments = json.loads(arguments)

    result = tool.invoke(arguments)

    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": result,
    }


def _build_final_answer_prompt(
    question: str,
    messages: list[dict[str, Any]],
) -> str:
    evidence_parts = []

    for message in messages:
        if message.get("role") != "tool":
            continue

        content = message.get("content", "")
        if content:
            evidence_parts.append(content)

    evidence = "\n\n".join(evidence_parts)

    return f"""
You are RepoPilot, an AI engineering assistant answering a question
about a software repository.

Answer the user's question using ONLY the repository evidence below.

Rules:
1. Read the actual code carefully.
2. Distinguish increment from decrement.
3. Distinguish different functions even when they appear in nearby chunks.
4. Do not infer behavior from function names alone.
5. Do not invent files, functions, behavior, or line numbers.
6. Do not claim something is the only occurrence unless the evidence
   establishes that.
7. If the evidence is insufficient, say:
   "The provided repository context is insufficient to answer this question."
8. Give a concise technical answer.
9. Do not search for more information.
10. Answer directly.

USER QUESTION:
{question}

REPOSITORY EVIDENCE:
{evidence}

FINAL ANSWER:
""".strip()


def build_repository_qa_graph(
    db,
    embedding_provider: EmbeddingProvider,
    llm_provider: LLMProvider,
):
    if not isinstance(llm_provider, GroqProvider):
        raise ValueError(
            "The current agent graph requires GroqProvider because "
            "native tool calling is implemented for Groq."
        )

    graph = StateGraph(RepositoryQAState)

    def agent_node(state):
        question = state.get("question", "").strip()
        repository_id = state.get("repository_id", "").strip()

        if not question:
            raise ValueError("Question cannot be empty.")

        if not repository_id:
            raise ValueError("Repository ID cannot be empty.")

        current_tool = create_search_repository_tool(
            db=db,
            embedding_provider=embedding_provider,
            repository_id=repository_id,
        )

        tool_definitions = [_build_tool_definition()]

        messages = state.get("messages")

        if not messages:
            messages = _build_initial_messages(question)

        print("\n========== REPOPILOT AGENT DEBUG ==========")
        print("\nMESSAGES:")
        print(messages)
        print("\nTOOLS:")
        print(tool_definitions)
        print("\n============================================\n")

        result = llm_provider.generate_with_tools(
            messages=messages,
            tools=tool_definitions,
        )

        tool_calls = result.get("tool_calls", [])

        if tool_calls:
            assistant_message = {
                "role": "assistant",
                "content": result.get("content"),
                "tool_calls": tool_calls,
            }

            updated_messages = [
                *messages,
                assistant_message,
            ]

            return {
                **state,
                "messages": updated_messages,
                "tool_calls": tool_calls,
                "answer": result.get("content"),
                "tool_call_count": state.get("tool_call_count", 0),
            }

        answer = (result.get("content") or "").strip()

        return {
            **state,
            "messages": messages,
            "answer": answer,
            "tool_calls": [],
        }

    def tool_node(state):
        repository_id = state.get("repository_id", "").strip()

        if not repository_id:
            raise ValueError("Repository ID cannot be empty.")

        current_tool = create_search_repository_tool(
            db=db,
            embedding_provider=embedding_provider,
            repository_id=repository_id,
        )

        tool_calls = state.get("tool_calls", [])

        if not tool_calls:
            return state

        messages = list(state.get("messages", []))
        tool_call_count = state.get("tool_call_count", 0)

        for tool_call in tool_calls:
            tool_message = _execute_tool_call(
                tool=current_tool,
                tool_call=tool_call,
            )

            messages.append(tool_message)
            tool_call_count += 1

        return {
            **state,
            "messages": messages,
            "tool_calls": [],
            "tool_call_count": tool_call_count,
        }

    def final_answer_node(state):
        question = state.get("question", "").strip()
        messages = list(state.get("messages", []))

        if not question:
            raise ValueError("Question cannot be empty.")

        final_prompt = _build_final_answer_prompt(
            question=question,
            messages=messages,
        )

        print("\n========== FINAL ANSWER NODE ==========")
        print("\nPROMPT:")
        print(final_prompt)
        print("\n=======================================\n")

        answer = llm_provider.generate(final_prompt).strip()

        return {
            **state,
            "answer": answer,
            "tool_calls": [],
            "context_sufficient": bool(answer),
        }

    def route_after_agent(state):
        tool_calls = state.get("tool_calls", [])
        tool_call_count = state.get("tool_call_count", 0)

        if not tool_calls:
            return "finish"

        if tool_call_count < MAX_TOOL_CALLS:
            return "execute_tool"

        return "final_answer"

    graph.add_node("agent", agent_node)
    graph.add_node("execute_tool", tool_node)
    graph.add_node("final_answer", final_answer_node)

    graph.add_edge(START, "agent")

    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "execute_tool": "execute_tool",
            "final_answer": "final_answer",
            "finish": END,
        },
    )

    graph.add_edge("execute_tool", "agent")
    graph.add_edge("final_answer", END)

    return graph.compile()