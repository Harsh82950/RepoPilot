from app.services.rag.context_builder import build_rag_context


def main():
    results = [
        {
            "file_path": "src/modules/wallet/wallet.repository.ts",
            "start_line": 141,
            "end_line": 220,
            "content": "await tx.wallet.update({ balance: { increment: amount } });",
        },
        {
            "file_path": "src/modules/wallet/wallet.repository.ts",
            "start_line": 71,
            "end_line": 150,
            "content": "await tx.wallet.update({ balance: { decrement: amount } });",
        },
    ]

    context = build_rag_context(results)

    print()
    print("=" * 80)
    print("RAG CONTEXT TEST")
    print("=" * 80)
    print(context)
    print("=" * 80)


if __name__ == "__main__":
    main()