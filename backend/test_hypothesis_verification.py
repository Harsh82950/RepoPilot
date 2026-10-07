from app.services.agents.hypothesis_verification import (
    verify_hypotheses,
)
from app.services.llm.groq_provider import GroqProvider


def main():
    llm_provider = GroqProvider(
        model_name="openai/gpt-oss-120b"
    )

    hypotheses = [
        "The refund repository is missing wallet balance update logic.",
        "walletRefundAmount may be calculated incorrectly.",
        "The refund flow contains wallet balance update logic.",
    ]

    evidence = """
    src/modules/refund/refund.service.ts calculates
    walletRefundAmount and passes it to refundRepository.processRefund.

    src/modules/refund/refund.repository.ts contains:

    if (params.walletRefundAmount > 0) {
        updatedWallet = await tx.wallet.update({
            where: { id: params.walletId },
            data: {
                balance: {
                    increment: params.walletRefundAmount
                }
            }
        });
    }

    The repository also creates a wallet transaction with
    type "REFUND" and description "Refund credited to wallet".

    The available source evidence does not establish whether
    the calculation of walletRefundAmount is incorrect.
    """

    result = verify_hypotheses(
        hypotheses=hypotheses,
        evidence=evidence,
        llm_provider=llm_provider,
    )

    print("=" * 80)
    print("HYPOTHESIS VERIFICATION RESULT")
    print("=" * 80)

    for evaluation in result["evaluations"]:
        print()
        print("Hypothesis:")
        print(evaluation["hypothesis"])

        print("Status:")
        print(evaluation["status"])

        print("Reason:")
        print(evaluation["reason"])


if __name__ == "__main__":
    main()