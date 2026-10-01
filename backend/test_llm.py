from app.services.llm.mock_llm_provider import MockLLMProvider


def main():
    llm = MockLLMProvider()

    prompt = "Where is the wallet balance updated?"

    response = llm.generate(prompt)

    print()
    print("=" * 60)
    print("LLM PROVIDER TEST")
    print("=" * 60)
    print("Prompt:")
    print(prompt)
    print()
    print("Response:")
    print(response)
    print("=" * 60)


if __name__ == "__main__":
    main()