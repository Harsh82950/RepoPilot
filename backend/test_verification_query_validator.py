from app.services.agents.verification_query_validator import (
    is_source_code_query,
    validate_verification_queries,
)


def main():
    allowed_queries = [
        "Find where walletRefundAmount is calculated.",
        "Find where processRefund receives walletRefundAmount.",
        "Find where paymentOrder.walletAmountUsed is assigned.",
    ]

    rejected_queries = [
        "Determine the runtime value of walletRefundAmount.",
        "Check the database value of walletRefundAmount.",
        "Check production logs for the refund.",
        "Set a breakpoint in processRefund.",
        "Find the actual value returned by the API.",
    ]

    print("Allowed query tests:")

    for query in allowed_queries:
        result = is_source_code_query(query)
        print(f"{result} -> {query}")

    print("\nRejected query tests:")

    for query in rejected_queries:
        result = is_source_code_query(query)
        print(f"{result} -> {query}")

    print("\nFiltered queries:")

    all_queries = allowed_queries + rejected_queries

    filtered = validate_verification_queries(all_queries)

    for query in filtered:
        print(f"- {query}")

    print("\nExpected:")
    print("- 3 allowed queries")
    print("- 5 rejected queries")
    print("- 3 queries remaining after filtering")


if __name__ == "__main__":
    main()