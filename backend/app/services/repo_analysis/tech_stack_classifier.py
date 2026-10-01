import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from app.services.repo_ingestion.file_scanner import ScannedFile


@dataclass
class TechStackResult:
    primary_language: str | None
    primary_framework: str | None
    tech_stack: dict[str, list[str]]


PACKAGE_TECHNOLOGIES = {
    "express": ("frameworks", "Express"),
    "fastapi": ("frameworks", "FastAPI"),
    "django": ("frameworks", "Django"),
    "flask": ("frameworks", "Flask"),
    "next": ("frameworks", "Next.js"),
    "react": ("frameworks", "React"),
    "vue": ("frameworks", "Vue"),
    "@nestjs/core": ("frameworks", "NestJS"),
    "prisma": ("orms", "Prisma"),
    "@prisma/client": ("orms", "Prisma"),
    "sqlalchemy": ("orms", "SQLAlchemy"),
    "typeorm": ("orms", "TypeORM"),
    "sequelize": ("orms", "Sequelize"),
    "redis": ("caches", "Redis"),
    "ioredis": ("caches", "Redis"),
    "jest": ("testing", "Jest"),
    "supertest": ("testing", "Supertest"),
    "pytest": ("testing", "Pytest"),
    "k6": ("testing", "k6"),
    "pg": ("databases", "PostgreSQL"),
    "psycopg": ("databases", "PostgreSQL"),
    "psycopg2": ("databases", "PostgreSQL"),
    "mysql2": ("databases", "MySQL"),
    "mongoose": ("databases", "MongoDB"),
}


PYTHON_TECHNOLOGIES = {
    "fastapi": ("frameworks", "FastAPI"),
    "django": ("frameworks", "Django"),
    "flask": ("frameworks", "Flask"),
    "sqlalchemy": ("orms", "SQLAlchemy"),
    "prisma": ("orms", "Prisma"),
    "redis": ("caches", "Redis"),
    "pytest": ("testing", "Pytest"),
    "psycopg": ("databases", "PostgreSQL"),
    "psycopg2": ("databases", "PostgreSQL"),
    "pymongo": ("databases", "MongoDB"),
}


def create_empty_tech_stack() -> dict[str, set[str]]:
    return {
        "languages": set(),
        "frameworks": set(),
        "databases": set(),
        "orms": set(),
        "caches": set(),
        "testing": set(),
        "infrastructure": set(),
    }


def detect_languages(
    scanned_files: list[ScannedFile],
) -> tuple[list[str], str | None]:
    language_counts = Counter(
        scanned_file.language
        for scanned_file in scanned_files
        if scanned_file.language is not None
        and scanned_file.file_type == "code"
    )

    languages = [
        language
        for language, _ in language_counts.most_common()
    ]

    primary_language = (
        languages[0]
        if languages
        else None
    )

    return languages, primary_language


def add_detected_technology(
    tech_stack: dict[str, set[str]],
    technology: tuple[str, str],
) -> None:
    category, name = technology

    tech_stack[category].add(name)


def inspect_package_json(
    repository_root: Path,
    tech_stack: dict[str, set[str]],
) -> None:
    package_json_path = repository_root / "package.json"

    if not package_json_path.exists():
        return

    try:
        package_data = json.loads(
            package_json_path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return

    dependencies = package_data.get(
        "dependencies",
        {},
    )

    dev_dependencies = package_data.get(
        "devDependencies",
        {},
    )

    package_names = {
        *dependencies.keys(),
        *dev_dependencies.keys(),
    }

    for package_name in package_names:
        technology = PACKAGE_TECHNOLOGIES.get(
            package_name.lower()
        )

        if technology is not None:
            add_detected_technology(
                tech_stack,
                technology,
            )


def inspect_python_dependencies(
    repository_root: Path,
    tech_stack: dict[str, set[str]],
) -> None:
    requirements_path = (
        repository_root / "requirements.txt"
    )

    if not requirements_path.exists():
        return

    try:
        lines = requirements_path.read_text(
            encoding="utf-8"
        ).splitlines()
    except (
        OSError,
        UnicodeDecodeError,
    ):
        return

    for line in lines:
        package_name = (
            line.strip()
            .lower()
            .split("==")[0]
            .split(">=")[0]
            .split("<=")[0]
            .split("~=")[0]
        )

        technology = PYTHON_TECHNOLOGIES.get(
            package_name
        )

        if technology is not None:
            add_detected_technology(
                tech_stack,
                technology,
            )


def inspect_repository_files(
    repository_root: Path,
    tech_stack: dict[str, set[str]],
) -> None:
    if (
        repository_root / "Dockerfile"
    ).exists():
        tech_stack["infrastructure"].add(
            "Docker"
        )

    if (
        repository_root / "docker-compose.yml"
    ).exists() or (
        repository_root / "docker-compose.yaml"
    ).exists():
        tech_stack["infrastructure"].add(
            "Docker Compose"
        )

    if (
        repository_root
        / "prisma"
        / "schema.prisma"
    ).exists():
        tech_stack["orms"].add(
            "Prisma"
        )

        inspect_prisma_schema(
            repository_root,
            tech_stack,
        )


def inspect_prisma_schema(
    repository_root: Path,
    tech_stack: dict[str, set[str]],
) -> None:
    prisma_schema_path = (
        repository_root
        / "prisma"
        / "schema.prisma"
    )

    try:
        content = prisma_schema_path.read_text(
            encoding="utf-8"
        ).lower()
    except (
        OSError,
        UnicodeDecodeError,
    ):
        return

    if 'provider = "postgresql"' in content:
        tech_stack["databases"].add(
            "PostgreSQL"
        )

    if 'provider = "mysql"' in content:
        tech_stack["databases"].add(
            "MySQL"
        )

    if 'provider = "mongodb"' in content:
        tech_stack["databases"].add(
            "MongoDB"
        )


def determine_primary_framework(
    tech_stack: dict[str, set[str]],
) -> str | None:
    framework_priority = [
        "FastAPI",
        "Django",
        "Flask",
        "NestJS",
        "Express",
        "Next.js",
        "React",
        "Vue",
    ]

    for framework in framework_priority:
        if framework in tech_stack["frameworks"]:
            return framework

    return None


def classify_tech_stack(
    repository_path: str,
    scanned_files: list[ScannedFile],
) -> TechStackResult:
    repository_root = Path(
        repository_path
    ).resolve()

    tech_stack = create_empty_tech_stack()

    languages, primary_language = detect_languages(
        scanned_files
    )

    tech_stack["languages"].update(
        languages
    )

    inspect_package_json(
        repository_root,
        tech_stack,
    )

    inspect_python_dependencies(
        repository_root,
        tech_stack,
    )

    inspect_repository_files(
        repository_root,
        tech_stack,
    )

    primary_framework = determine_primary_framework(
        tech_stack
    )

    serialized_tech_stack = {
        category: sorted(values)
        for category, values in tech_stack.items()
    }

    return TechStackResult(
        primary_language=primary_language,
        primary_framework=primary_framework,
        tech_stack=serialized_tech_stack,
    )