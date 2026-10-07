from app.services.agents.bug_file_inspection import (
    inspect_repository_files,
)


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"

REPOSITORY_PATH = (
    r"C:\Users\HP\Desktop\repopilot\backend"
    r"\storage\repos\c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"
)


def main():
    state = {
        "repository_id": REPOSITORY_ID,
        "verification_queries": [
            (
                "Inspect "
                "src/modules/refund/refund.repository.ts "
                "lines 72-120"
            ),
        ],
    }

    result = inspect_repository_files(
        state=state,
        repository_path=REPOSITORY_PATH,
    )

    print("\n" + "=" * 80)
    print("BUG FILE INSPECTION TEST")
    print("=" * 80)

    print("\nInspection count:")
    print(result["file_inspection_count"])

    print("\nInspection calls:")
    for call in result["file_inspection_calls"]:
        print(call)

    print("\nInspection results:")
    for inspection in result["file_inspection_results"]:
        print("\nQuery:")
        print(inspection["query"])

        print("\nContent:")
        print(inspection["content"])


if __name__ == "__main__":
    main()