from app.services.agents.repository_file_tool import read_repository_file


REPOSITORY_PATH = r"C:\Users\HP\Desktop\repopilot\backend\storage\repos\c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


def main():
    result = read_repository_file(
        repository_path=REPOSITORY_PATH,
        file_path="src/modules/refund/refund.repository.ts",
        start_line=72,
        end_line=154,
    )

    print("\n" + "=" * 80)
    print("PROCESS REFUND INSPECTION")
    print("=" * 80)
    print(result)


if __name__ == "__main__":
    main()