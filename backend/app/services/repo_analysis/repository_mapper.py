from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from app.services.repo_ingestion.file_scanner import ScannedFile


@dataclass
class RepositoryModule:
    name: str
    path: str
    module_type: str
    file_count: int


@dataclass
class RepositoryMapResult:
    important_modules: list[dict]
    probable_entrypoints: list[str]
    file_module_types: dict[str, str]


ENTRYPOINT_FILE_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "main.ts",
    "app.ts",
    "server.ts",
    "index.ts",
    "main.js",
    "app.js",
    "server.js",
    "index.js",
}


FEATURE_DIRECTORY_NAMES = {
    "modules",
    "features",
    "domains",
}


INFRASTRUCTURE_DIRECTORY_NAMES = {
    "db",
    "database",
    "redis",
    "cache",
    "queue",
    "queues",
    "worker",
    "workers",
    "messaging",
    "infrastructure",
}


CONFIG_DIRECTORY_NAMES = {
    "config",
    "configs",
    "settings",
}


TEST_DIRECTORY_NAMES = {
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
}


def detect_probable_entrypoints(
    scanned_files: list[ScannedFile],
) -> list[str]:
    entrypoints: list[str] = []

    ignored_parent_directories = {
        "routes",
        "controllers",
        "services",
        "models",
        "schemas",
        "middleware",
        "middlewares",
        "utils",
        "helpers",
        "modules",
        "features",
        "domains",
    }

    for scanned_file in scanned_files:
        relative_path = Path(
            scanned_file.relative_path
        )

        file_name = relative_path.name.lower()

        if file_name not in ENTRYPOINT_FILE_NAMES:
            continue

        parent_parts = {
            part.lower()
            for part in relative_path.parts[:-1]
        }

        if (
            file_name in {"index.ts", "index.js"}
            and parent_parts.intersection(
                ignored_parent_directories
            )
        ):
            continue

        entrypoints.append(
            scanned_file.relative_path
        )

    return sorted(
        entrypoints,
        key=entrypoint_priority,
    )

def entrypoint_priority(file_path: str) -> tuple[int, int, str]:
    path = Path(file_path)

    name_priority = {
        "server.ts": 0,
        "server.js": 0,
        "main.py": 0,
        "main.ts": 0,
        "main.js": 0,
        "app.ts": 1,
        "app.js": 1,
        "app.py": 1,
        "index.ts": 2,
        "index.js": 2,
        "manage.py": 2,
    }

    return (
        name_priority.get(
            path.name.lower(),
            10,
        ),
        len(path.parts),
        file_path,
    )


def detect_file_module_type(
    scanned_file: ScannedFile,
) -> str:
    relative_path = Path(
        scanned_file.relative_path
    )

    path_parts = [
        part.lower()
        for part in relative_path.parts
    ]

    if any(
        part in TEST_DIRECTORY_NAMES
        for part in path_parts
    ):
        return "test"

    if any(
        part in CONFIG_DIRECTORY_NAMES
        for part in path_parts
    ):
        return "config"

    if any(
        part in INFRASTRUCTURE_DIRECTORY_NAMES
        for part in path_parts
    ):
        return "infrastructure"

    if any(
        part in FEATURE_DIRECTORY_NAMES
        for part in path_parts
    ):
        return "feature"

    if scanned_file.file_type == "config":
        return "config"

    if scanned_file.file_type == "doc":
        return "documentation"

    if scanned_file.file_type == "test":
        return "test"

    if scanned_file.file_type == "code":
        return "source"

    return "other"


def detect_feature_modules(
    scanned_files: list[ScannedFile],
) -> list[RepositoryModule]:
    module_files: dict[str, list[str]] = defaultdict(list)

    for scanned_file in scanned_files:
        relative_path = Path(
            scanned_file.relative_path
        )

        parts = list(relative_path.parts)

        lowered_parts = [
            part.lower()
            for part in parts
        ]

        for index, part in enumerate(lowered_parts):
            if (
                part in FEATURE_DIRECTORY_NAMES
                and index + 1 < len(parts)
            ):
                module_path = Path(
                    *parts[: index + 2]
                ).as_posix()

                module_files[module_path].append(
                    scanned_file.relative_path
                )

                break

    modules = [
        RepositoryModule(
            name=Path(module_path).name,
            path=module_path,
            module_type="feature",
            file_count=len(files),
        )
        for module_path, files in module_files.items()
    ]

    return sorted(
        modules,
        key=lambda module: (
            -module.file_count,
            module.name,
        ),
    )


def detect_structural_modules(
    scanned_files: list[ScannedFile],
) -> list[RepositoryModule]:
    module_counts: Counter[tuple[str, str]] = Counter()

    for scanned_file in scanned_files:
        relative_path = Path(
            scanned_file.relative_path
        )

        parts = list(relative_path.parts)

        for index, part in enumerate(parts[:-1]):
            lowered_part = part.lower()

            if lowered_part in INFRASTRUCTURE_DIRECTORY_NAMES:
                module_path = Path(
                    *parts[: index + 1]
                ).as_posix()

                module_counts[
                    (module_path, "infrastructure")
                ] += 1

                break

            if lowered_part in CONFIG_DIRECTORY_NAMES:
                module_path = Path(
                    *parts[: index + 1]
                ).as_posix()

                module_counts[
                    (module_path, "config")
                ] += 1

                break

    modules = [
        RepositoryModule(
            name=Path(module_path).name,
            path=module_path,
            module_type=module_type,
            file_count=file_count,
        )
        for (
            module_path,
            module_type,
        ), file_count in module_counts.items()
    ]

    return sorted(
        modules,
        key=lambda module: (
            module.module_type,
            -module.file_count,
            module.name,
        ),
    )


def serialize_module(
    module: RepositoryModule,
) -> dict:
    return {
        "name": module.name,
        "path": module.path,
        "module_type": module.module_type,
        "file_count": module.file_count,
    }


def map_repository(
    scanned_files: list[ScannedFile],
) -> RepositoryMapResult:
    probable_entrypoints = detect_probable_entrypoints(
        scanned_files
    )

    feature_modules = detect_feature_modules(
        scanned_files
    )

    structural_modules = detect_structural_modules(
        scanned_files
    )

    all_modules = [
        *feature_modules,
        *structural_modules,
    ]

    file_module_types = {
        scanned_file.relative_path: detect_file_module_type(
            scanned_file
        )
        for scanned_file in scanned_files
    }

    return RepositoryMapResult(
        important_modules=[
            serialize_module(module)
            for module in all_modules
        ],
        probable_entrypoints=probable_entrypoints,
        file_module_types=file_module_types,
    )