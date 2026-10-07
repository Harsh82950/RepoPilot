from app.services.llm.groq_provider import GroqProvider


def main():
    provider = GroqProvider()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a repository analysis assistant. "
                "When repository information is needed, use the "
                "search_repository tool."
            ),
        },
        {
            "role": "user",
            "content": (
                "Where is balance.increment used in the wallet repository?"
            ),
        },
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_repository",
                "description": (
                    "Search the repository for relevant files, "
                    "functions, and code."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The repository search query."
                            ),
                        }
                    },
                    "required": ["query"],
                },
            },
        }
    ]

    result = provider.generate_with_tools(
        messages=messages,
        tools=tools,
    )

    print()
    print("=" * 80)
    print("GROQ TOOL-CALL TEST")
    print("=" * 80)
    print()

    print("Content:")
    print(result["content"])

    print()
    print("Tool calls:")
    print(result["tool_calls"])

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()