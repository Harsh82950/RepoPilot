from app.services.llm.ollama_provider import OllamaProvider


def main():
    llm = OllamaProvider()

    prompt = """
Explain what a REST API is in one or two sentences.
Keep the explanation simple.
""".strip()

    print()
    print("=" * 80)
    print("OLLAMA PROVIDER TEST")
    print("=" * 80)

    print()
    print("Sending prompt to Ollama...")
    print()

    response = llm.generate(prompt)

    print("Response:")
    print("-" * 80)
    print(response)

    print()
    print("=" * 80)
    print("OLLAMA PROVIDER TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()