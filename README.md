# RepoPilot 🚀

> AI-powered codebase assistant for understanding, searching, and reasoning about software repositories.

RepoPilot is an AI engineering assistant designed to help developers understand unfamiliar codebases faster.

Given a GitHub repository or uploaded project, RepoPilot analyzes the repository structure, identifies important modules, indexes the source code, and uses Retrieval-Augmented Generation (RAG) to answer questions using relevant repository context.

The long-term goal is to evolve RepoPilot into a repository-aware engineering assistant capable of answering codebase questions, investigating bugs, planning features, and analyzing pull requests.

---

## ✨ Features

### 📦 Repository Ingestion

- GitHub repository ingestion
- ZIP/project upload support
- Recursive source-file scanning
- Configurable ignore rules
- Detection of relevant source and documentation files

### 🔍 Repository Analysis

RepoPilot analyzes a repository to identify:

- Primary programming language
- Frameworks
- Databases
- ORMs
- Caches
- Testing frameworks
- Infrastructure and development tools

### 🗺️ Repository Mapping

RepoPilot builds a structural understanding of the repository, including:

- Project entry points
- Important modules
- Feature directories
- Configuration files
- Test files
- Documentation
- Source-code distribution

### ✂️ Code-Aware Chunking

Source code is divided into meaningful chunks using code structure and boundaries rather than simply splitting text into arbitrary pieces.

Each chunk stores:

- Repository ID
- File path
- Chunk index
- Source content
- Start line
- End line

### 🧠 Semantic Embeddings

Repository chunks are converted into vector embeddings using:

**Qwen3-Embedding-0.6B**

- 1024-dimensional embeddings
- Normalized vectors
- Stored using PostgreSQL + pgvector

### 🔎 Hybrid Retrieval

RepoPilot combines multiple retrieval signals:

- Semantic similarity
- Keyword matching
- Code/action-aware signals

This allows repository questions such as:

```text
Where is the wallet balance updated?

🏗️ Architecture

                         GitHub / ZIP
                              │
                              ▼
                    ┌──────────────────┐
                    │ Repository       │
                    │ Ingestion        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ File Scanner &   │
                    │ Ignore Rules     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Repository       │
                    │ Mapper           │
                    │ + Tech Detection │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Code-Aware       │
                    │ Chunking         │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Qwen3 Embeddings │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ PostgreSQL       │
                    │ + pgvector       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Hybrid Retrieval │
                    │ Semantic +       │
                    │ Keyword + Action │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ RAG Context      │
                    │ Builder          │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ LLM Provider     │
                    │ Qwen2.5-Coder    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Repository-      │
                    │ Aware Answer     │
                    └──────────────────┘


📁 Project Structure
                    repopilot/
│
├── backend/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │
│   │   ├── db/
│   │   │
│   │   ├── models/
│   │   │
│   │   ├── schemas/
│   │   │
│   │   └── services/
│   │       │
│   │       ├── chunking/
│   │       ├── embeddings/
│   │       ├── llm/
│   │       ├── rag/
│   │       ├── repo_analysis/
│   │       ├── repo_ingestion/
│   │       └── retrieval/
│   │
│   ├── retrieval_eval.py
│   ├── real_rag_eval.py
│   └── tests/
│
└── docker-compose.yml

1. Clone the Repository
git clone <https://github.com/Harsh82950/RepoPilot>
cd repopilot

2. Start PostgreSQL + pgvector
Make sure Docker Desktop is running.
docker compose up -d

Verify the container:
docker ps

3. Create the Python Environment
cd backend

python -m venv .venv

Windows
.venv\Scripts\Activate.ps1

Linux / macOS
source .venv/bin/activate

4. Install Dependencies
pip install -r requirements.txt

5. Start the FastAPI Server
uvicorn app.main:app --reload

The API will be available at:
http://127.0.0.1:8000

Interactive API documentation:
http://127.0.0.1:8000/docs

🤖 Local LLM Setup
RepoPilot currently uses Ollama for local LLM inference.
Pull the development model:
ollama pull qwen2.5-coder:1.5b

Verify that the model is available:
ollama list

The current provider communicates with:
http://localhost:11434/api/generate

The LLM provider is intentionally abstracted so that other models and providers can be integrated later.