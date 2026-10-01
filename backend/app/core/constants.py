REPO_STATUS_QUEUED = "queued"
REPO_STATUS_PROCESSING = "processing"
REPO_STATUS_READY = "ready"
REPO_STATUS_FAILED = "failed"

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCESS = "success"
JOB_STATUS_FAILED = "failed"

SOURCE_TYPE_GITHUB = "github"
SOURCE_TYPE_ZIP = "zip"
SOURCE_TYPE_UPLOAD = "upload"

DEFAULT_TOP_K = 8

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
}

IGNORED_FILE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".mp4",
    ".mp3",
    ".wav",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
}

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".cs",
}

DOC_EXTENSIONS = {
    ".md",
    ".txt",
}

CONFIG_FILE_NAMES = {
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "requirements.txt",
    "pyproject.toml",
    "docker-compose.yml",
    "Dockerfile",
    ".env.example",
}