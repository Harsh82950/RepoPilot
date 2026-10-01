from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine

# Import models here so they are registered with Base.metadata.
from app.models.analysis_job import AnalysisJob
from app.models.repository import Repository
from app.models.repository_chunk import RepositoryChunk
from app.models.repository_file import RepositoryFile
from app.models.repository_summary import RepositorySummary


def init_db() -> None:
    with engine.begin() as connection:
        connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")