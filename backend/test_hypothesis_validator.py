from app.services.agents.hypothesis_validator import (
    classify_hypothesis,
    validate_hypotheses,
)


def main():
    evidence = """
    The refund service calculates walletRefundAmount and passes it
    to processRefund.

    processRefund checks whether walletRefundAmount is greater than
    zero. When it is greater than zero, the wallet balance is updated
    using increment(walletRefundAmount).

    The wallet transaction is also created with type REFUND.
    """

    confirmed_hypothesis = (
        "The refund flow contains wallet balance update logic."
    )

    disproved_hypothesis = (
        "The refund repository is missing wallet balance update logic."
    )

    unresolved_hypothesis = (
        "walletRefundAmount may be calculated incorrectly."
    )

    print("Individual tests:")
    print(
        "Confirmed:",
        classify_hypothesis(
            confirmed_hypothesis,
            evidence,
        ),
    )

    print(
        "Disproved:",
        classify_hypothesis(
            disproved_hypothesis,
            evidence,
        ),
    )

    print(
        "Unresolved:",
        classify_hypothesis(
            unresolved_hypothesis,
            evidence,
        ),
    )

    print("\nGrouped validation:")

    result = validate_hypotheses(
        [
            confirmed_hypothesis,
            disproved_hypothesis,
            unresolved_hypothesis,
        ],
        evidence,
    )

    print("Confirmed:")
    for item in result["confirmed"]:
        print(f"- {item}")

    print("\nDisproved:")
    for item in result["disproved"]:
        print(f"- {item}")

    print("\nUnresolved:")
    for item in result["unresolved"]:
        print(f"- {item}")


if __name__ == "__main__":
    main()