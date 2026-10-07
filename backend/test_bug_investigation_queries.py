from app.services.agents.bug_investigation_queries import (
    build_bug_search_queries,
)


def main():
    state = {
        "error_type": "TypeError",
        "error_message": (
            "TypeError: Cannot read properties of undefined"
        ),
        "extracted_functions": [
            "processRefund",
            "payOrder",
        ],
        "extracted_files": [
            "src/modules/refund/refund.repository.ts",
            "src/modules/payment/payment.service.ts",
        ],
    }

    result = build_bug_search_queries(state)

    print("\n=== Bug Search Queries ===")

    for index, query in enumerate(
        result["search_queries"],
        start=1,
    ):
        print(f"{index}. {query}")


if __name__ == "__main__":
    main()