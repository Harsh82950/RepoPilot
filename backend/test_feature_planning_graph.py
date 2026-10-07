import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.embeddings.embedding_service import (
    QwenEmbeddingProvider,
)
from app.services.agents.feature_planning_graph import (
    build_feature_planning_graph,
)
from app.services.llm.groq_provider import (
    GroqProvider,
)


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"

FEATURE_REQUEST = (
    "Add Redis caching for wallet balance"
)


def main():

    print(
        "Starting Feature Planning Agent test..."
    )

    print(
        "\nInitializing embedding provider..."
    )

    embedding_provider = QwenEmbeddingProvider()

    print(
        "Initializing planning model: GPT-OSS 20B..."
    )

    llm_provider = GroqProvider(
        model_name="openai/gpt-oss-20b",
        json_mode=True,
        max_completion_tokens=1200,
        reasoning_effort="low",
    )

    print(
        "Connecting to PostgreSQL..."
    )

    engine = create_engine(
        settings.DATABASE_URL
    )

    SessionLocal = sessionmaker(
        bind=engine
    )

    db = SessionLocal()

    try:

        print(
            "Building feature planning graph..."
        )

        graph = build_feature_planning_graph(
            db=db,
            embedding_provider=embedding_provider,
            llm_provider=llm_provider,
        )

        print(
            "\nRunning feature planning..."
        )

        result = graph.invoke(
            {
                "repository_id": REPOSITORY_ID,
                "feature_request": FEATURE_REQUEST,
            }
        )

        print(
            "\n"
            + "=" * 80
        )

        print(
            "FINAL FEATURE PLAN"
        )

        print(
            "=" * 80
        )

        plan = result.get(
            "plan",
            "",
        )

        if plan:

            try:
                parsed = json.loads(
                    plan
                )

                print(
                    json.dumps(
                        parsed,
                        indent=2,
                    )
                )

            except json.JSONDecodeError:

                print(plan)

        else:

            print(
                json.dumps(
                    {
                        "implementation_overview":
                            result.get(
                                "implementation_overview",
                                "",
                            ),
                        "affected_files":
                            result.get(
                                "affected_files",
                                [],
                            ),
                        "new_files":
                            result.get(
                                "new_files",
                                [],
                            ),
                        "implementation_steps":
                            result.get(
                                "implementation_steps",
                                [],
                            ),
                        "data_flow":
                            result.get(
                                "data_flow",
                                [],
                            ),
                        "risks":
                            result.get(
                                "risks",
                                [],
                            ),
                        "tests":
                            result.get(
                                "tests",
                                [],
                            ),
                        "assumptions":
                            result.get(
                                "assumptions",
                                [],
                            ),
                        "confidence":
                            result.get(
                                "confidence",
                                "Low",
                            ),
                    },
                    indent=2,
                )
            )

        print(
            "\n"
            + "=" * 80
        )

        print(
            "FEATURE PLANNING METADATA"
        )

        print(
            "=" * 80
        )

        print(
            f"Feature request: {FEATURE_REQUEST}"
        )

        print(
            "\nTool calls:"
        )

        print(
            json.dumps(
                result.get(
                    "tool_calls",
                    [],
                ),
                indent=2,
            )
        )

        print(
            "\nTool call count:",
            result.get(
                "tool_call_count",
                0,
            ),
        )

        print(
            "\nSearch queries:"
        )

        print(
            json.dumps(
                result.get(
                    "search_queries",
                    [],
                ),
                indent=2,
            )
        )

        print(
            "\nRetrieval results:",
            len(
                result.get(
                    "retrieval_results",
                    [],
                )
            ),
        )

        print(
            "\nConfidence:",
            result.get(
                "confidence",
                "Low",
            ),
        )

        print(
            "\nTest completed successfully."
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()