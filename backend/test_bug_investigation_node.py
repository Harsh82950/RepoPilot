from app.services.agents.bug_investigation_nodes import extract_bug_signals


def main():
    bug_report = """
    TypeError: Cannot read properties of undefined
    at processRefund (src/modules/refund/refund.repository.ts:84)
    at payOrder (src/modules/payment/payment.service.ts:142)
    """

    state = {
        "bug_report": bug_report,
    }

    result = extract_bug_signals(state)

    print("\n=== Bug Signal Extraction ===")
    print("Error type:", result["error_type"])
    print("Error message:", result["error_message"])
    print("Files:", result["extracted_files"])
    print("Functions:", result["extracted_functions"])
    print("Symbols:", result["extracted_symbols"])


if __name__ == "__main__":
    main()