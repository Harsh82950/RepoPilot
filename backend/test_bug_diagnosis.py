from app.services.agents.bug_diagnosis import diagnose_bug
from app.services.llm.groq_provider import GroqProvider


def main():
    state = {
        "bug_report": """
        Refund succeeds, but the customer wallet balance is not increasing.
        The refund API returns success, but the expected wallet credit is missing.
        """,
        "error_type": "",
        "error_message": "",
        "retrieval_results": [
            {
                "query": "processRefund",
                "content": """
                File: src/modules/refund/refund.repository.ts
                Lines: 71-150

                async processRefund(params: {
                  refundId: string;
                  paymentOrderId: string;
                  walletId: string;
                  totalRefundAmount: number;
                  walletRefundAmount: number;
                  gatewayRefundAmount: number;
                }) {
                  return prisma.$transaction(async (tx) => {
                    let updatedWallet =
                      await tx.wallet.findUniqueOrThrow({
                        where: { id: params.walletId }
                      });

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

                    await tx.walletTransaction.create({
                      data: {
                        walletId: params.walletId,
                        type: "REFUND",
                        amount: params.walletRefundAmount,
                        balanceAfter: updatedWallet.balance,
                        reservedAfter: updatedWallet.reservedBalance,
                        reference: params.refundId
                      }
                    });
                  });
                }
                """,
            },
            {
                "query": "refund service",
                "content": """
                File: src/modules/refund/refund.service.ts

                const result = await refundRepository.processRefund({
                  refundId: createdRefund.id,
                  paymentOrderId: order.id,
                  walletId: wallet.id,
                  totalRefundAmount: refundAmountInMinorUnits,
                  walletRefundAmount,
                  gatewayRefundAmount
                });
                """,
            },
        ],
    }

    llm_provider = GroqProvider()

    result = diagnose_bug(
        state=state,
        llm_provider=llm_provider,
    )

    print("\n=== Bug Diagnosis ===")

    print("\nLikely locations:")
    for location in result["likely_locations"]:
        print(location)

    print("\nEvidence:")
    print(result["diagnosis"])

    print("\nRoot cause:")
    print(result["root_cause"])

    print("\nHypotheses:")
    for hypothesis in result["hypotheses"]:
        print("-", hypothesis)

    print("\nConfidence:")
    print(result["confidence"])

    print("\nDebugging steps:")
    for index, step in enumerate(
        result["debugging_steps"],
        start=1,
    ):
        print(f"{index}. {step}")


if __name__ == "__main__":
    main()