from app.services.agents.diagnosis_consistency import (
    validate_diagnosis_output,
)


def main():
    evidence = """
    File: src/modules/refund/refund.service.ts

    File: src/modules/refund/refund.repository.ts

    The repository contains processRefund and updates
    the wallet balance.

    The service calls refundRepository.processRefund.
    """

    diagnosis = {
        "likely_locations": [
            {
                "file": "src/modules/refund/refund.repository.ts",
                "function": "processRefund",
                "reason": "Contains wallet balance update logic.",
            },
            {
                "file": "src/repositories/refund.repository.ts",
                "function": "processRefund",
                "reason": "This path is not present in the evidence.",
            },
        ],
        "confirmed_hypotheses": [],
        "root_cause": (
            "walletRefundAmount is definitely zero."
        ),
        "debugging_steps": [
            "Inspect processRefund source code.",
            "Check the runtime value of walletRefundAmount.",
            "Check production logs for the refund.",
            "Trace walletRefundAmount calculation in the service.",
        ],
    }

    result = validate_diagnosis_output(
        diagnosis_data=diagnosis,
        evidence=evidence,
    )

    print("=" * 80)
    print("CONSISTENCY VALIDATION RESULT")
    print("=" * 80)

    print("\nLikely locations:")
    for location in result["likely_locations"]:
        print(location)

    print("\nRoot cause:")
    print(result["root_cause"])

    print("\nDebugging steps:")
    for step in result["debugging_steps"]:
        print(f"- {step}")


if __name__ == "__main__":
    main()