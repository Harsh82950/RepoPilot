from app.services.agents.repository_file_tool import (
    create_open_repository_file_tool,
)


REPOSITORY_PATH = (
    r"C:\Users\HP\Desktop\repopilot\backend"
    r"\storage\repos\c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"
)


def main():
    open_file_tool = create_open_repository_file_tool(
        repository_path=REPOSITORY_PATH
    )

    print("\n" + "=" * 80)
    print("LANGCHAIN FILE TOOL TEST")
    print("=" * 80)

    print("\nTool name:")
    print(open_file_tool.name)

    print("\nTool description:")
    print(open_file_tool.description)

    print("\nTool arguments:")
    print(open_file_tool.args)

    result = open_file_tool.invoke(
        {
            "file_path": "src/modules/refund/refund.repository.ts",
            "start_line": 72,
            "end_line": 120,
        }
    )

    print("\n" + "=" * 80)
    print("TOOL RESULT")
    print("=" * 80)
    print(result)


if __name__ == "__main__":
    main()