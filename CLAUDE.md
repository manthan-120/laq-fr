# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A minimal, privacy-friendly Retrieval-Augmented Generation (RAG) system that runs entirely locally without external API calls. The system processes Legislative Assembly Question (LAQ) PDFs, extracts Q&A pairs using LLMs, stores them in a vector database, and enables semantic search and chat interactions.

**Tech Stack:**
- **LLM:** Mistral (via Ollama)
- **Embeddings:** nomic-embed-text (via Ollama)
- **Vector DB:** ChromaDB with cosine similarity
- **Document Conversion:** Docling (PDF to Markdown)
- **Validation:** Pydantic for data schema validation
- **Language:** Python 3.10+

## Running the Application

The application can be run in two ways:

### Option A: Docker Deployment (Recommended for Demos)

**Quick Start:**
```bash
# Ensure Ollama is running on host with models installed
ollama pull mistral
ollama pull nomic-embed-text

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

See the [Docker Deployment](#docker-deployment) section below for comprehensive documentation.

### Option B: Native Python Setup

**Prerequisites:**
Ollama must be installed and running with required models:
```bash
# Start Ollama and pull required models
ollama pull mistral
ollama pull nomic-embed-text
```

**Setup:**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure environment variables
cp .env.example .env
# Edit .env to customize settings

# Run the application
python main.py
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Sample PDFs
Test PDFs are located in `sample_pdfs/` directory (sample1.pdf, sample2.pdf, sample3.pdf).

## Architecture

### Modular Design
The application consists of a React frontend, FastAPI backend, and ChromaDB vector database. Both CLI and web interfaces are supported.

```
minimal-local-RAG/
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API service layer
│   │   └── types/           # TypeScript interfaces
│   ├── Dockerfile           # Multi-stage React build
│   ├── nginx.conf           # Production Nginx config
│   └── package.json
├── backend/                  # FastAPI backend
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # ChromaDB operations
│   ├── embeddings.py        # Embedding generation
│   ├── pdf_processor.py     # PDF to structured data pipeline
│   ├── rag.py               # Search and chat logic
│   ├── Dockerfile           # Python 3.11 backend image
│   └── requirements.txt
├── tests/                    # Unit tests
│   ├── test_config.py
│   ├── test_pdf_processor.py
│   └── README.md
├── docker-compose.yml        # Service orchestration
├── README.DOCKER.md          # Docker deployment guide
├── CLAUDE.md                 # This file
└── README.md
```

### Core Components

The application consists of backend Python modules and a React frontend.

#### Backend Components

#### 1. Configuration (`backend/config.py`)
- **Config dataclass** with environment variable support via `python-dotenv`
- Validates all settings on initialization (thresholds, top-k values, temperature)
- Creates database directory automatically
- All configurable parameters are documented in `.env.example`

#### 2. Database (`database.py`)
- **LAQDatabase class** encapsulates all ChromaDB operations
- Batch insertion support for better performance
- Duplicate ID detection before insertion
- Relevance filtering based on similarity threshold
- Custom exceptions: `DatabaseError`

#### 3. Embeddings (`embeddings.py`)
- **EmbeddingService class** handles embedding generation
- Verifies Ollama connection on initialization
- Batch embedding support for multiple texts
- Custom exceptions: `EmbeddingError`, `OllamaConnectionError`, `OllamaModelNotFoundError`
- Provides actionable error messages (e.g., "Run: ollama pull nomic-embed-text")

#### 4. PDF Processor (`pdf_processor.py`)
- **Pydantic models** for data validation: `QAPair`, `LAQData`
- **PDFProcessor class** handles PDF → structured data pipeline
- File validation (existence, extension, size warnings)
- JSON extraction with fallback regex parsing
- Automatic schema validation via Pydantic
- Custom exception: `PDFProcessingError`

#### 5. RAG Service (`rag.py`)
- **RAGService class** provides search and chat capabilities
- Improved chat prompt with clear instructions and citation requirements
- Context building with proper formatting and LAQ separation
- Match quality statistics and color-coded relevance indicators
- Configurable temperature (0.1) for factual responses

#### 6. CLI (`cli.py`)
- **CLI class** provides interactive menu-driven interface
- Progress bars using `tqdm` for long operations (embedding generation)
- Enhanced error handling with user-friendly messages
- Database info display
- Formatted output for search results and extracted data

#### 7. FastAPI Backend (`backend/main.py`)
- **FastAPI application** with REST API endpoints
- CORS middleware for frontend communication
- Health check endpoint: `GET /health`
- API endpoints:
  - `POST /api/upload` - Upload and process PDF files
  - `POST /api/search` - Semantic search over LAQs
  - `POST /api/chat` - Chat with RAG context
  - `GET /api/stats` - Database statistics
- Comprehensive error handling with specific exception types
- Helpful error messages for common issues (Ollama not running, models not found)

#### Frontend Components

#### 8. React Frontend (`frontend/src/`)
- **TypeScript React application** built with Vite
- Component structure:
  - `App.tsx` - Main application layout and routing
  - `Upload.tsx` - PDF upload interface with drag-and-drop
  - `Search.tsx` - Semantic search interface
  - `Chat.tsx` - Conversational RAG interface
  - `Stats.tsx` - Database statistics dashboard
- **API Service Layer** (`services/api.ts`) - Centralized API calls
- **TypeScript Interfaces** (`types/`) - Type-safe data models
- Modern UI with Tailwind CSS
- Responsive design for mobile and desktop

### Core Pipeline Flow

1. **PDF Upload Workflow:**
   - User provides PDF path
   - `PDFProcessor.validate_pdf_file()` checks file existence, type, and size
   - `PDFProcessor.extract_markdown_from_pdf()` converts PDF → Markdown via Docling
   - `PDFProcessor.structure_laqs_with_mistral()` extracts structured JSON with Pydantic validation
   - Display extracted data to user for review
   - `EmbeddingService.embed_qa_pairs()` generates embeddings with progress bar
   - `LAQDatabase.store_qa_pairs()` performs batch insertion into ChromaDB

2. **Search Workflow:**
   - User enters query
   - `EmbeddingService.embed_text()` generates query embedding
   - `RAGService.search()` retrieves relevant LAQs with relevance filtering
   - Results displayed with match quality stats and color-coded indicators

3. **Chat Workflow:**
   - User enters question
   - `RAGService.chat()` retrieves top-k LAQs and builds formatted context
   - Improved prompt instructs LLM to cite sources and acknowledge missing information
   - Response generated with low temperature (0.1) for factual accuracy
   - Source LAQs displayed with similarity scores

### Data Storage

**ChromaDB Collection:** `laqs`
- **Path:** Configurable via `DB_PATH` (default: `./laq_db`)
- **Similarity metric:** Cosine
- **Document format:** `"Q: {question}\nA: {answer}"`
- **Metadata fields:** pdf, pdf_title, laq_num, qa_pair_num, type, question, answer, minister, date, attachments
- **Document IDs:** `{pdf_stem}_{laq_number}_qa{index}`

### Pydantic Models

**QAPair:**
```python
class QAPair(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
```

**LAQData:**
```python
class LAQData(BaseModel):
    pdf_title: str
    laq_type: str
    laq_number: str
    minister: str
    date: str
    qa_pairs: List[QAPair] = Field(min_items=1)
    tabled_by: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
```

All LAQ data is validated against these schemas, ensuring data quality.

### LLM Prompt Engineering

#### Extraction Prompt (`pdf_processor.py`)
Detailed prompt for extracting structured LAQ data with:
- Clear output format specification with example
- Rules for handling sub-questions (a), (b), (c)
- Instructions to preserve exact wording
- JSON-only output requirement

#### Chat Prompt (`rag.py`)
Improved conversational prompt with:
- System instructions defining the assistant's role
- Context section with formatted LAQs
- 7 specific instructions including:
  - Answer only from provided context
  - Cite LAQ numbers explicitly
  - Acknowledge missing information
  - Maintain professional tone
  - Reference attachments when mentioned

### Error Handling

All modules use custom exception hierarchies:
- `DatabaseError` - Database operation failures
- `EmbeddingError` - Embedding generation failures
  - `OllamaConnectionError` - Cannot connect to Ollama
  - `OllamaModelNotFoundError` - Model not available
- `PDFProcessingError` - PDF processing failures
- `RAGError` - Search and chat failures

Error messages are actionable and guide users to solutions (e.g., "Run: ollama serve").

### Configuration

All settings can be customized via environment variables (see `.env.example`):
- Model selection (LLM and embedding models)
- Retrieval parameters (top-k, similarity threshold)
- Processing limits (chunk size, metadata length)
- LLM generation parameters (temperature, top-p)
- Ollama connection settings

### Match Quality Scoring
Search results use distance-to-similarity conversion: `score = (1 - distance) * 100`
- 🟢 80%+: Strong match
- 🟡 60-79%: Moderate match
- 🔴 <60%: Weak match

### Testing

Unit tests are located in `tests/`:
- `test_config.py` - Configuration validation tests
- `test_pdf_processor.py` - Pydantic model and PDF validation tests

Run tests with `pytest tests/` (requires `pytest` and `pytest-cov`).

### Key Improvements Over Original

1. **Modularity:** Split into 7 focused modules instead of single 400-line file
2. **Type Safety:** Pydantic models for data validation
3. **Error Handling:** Custom exception hierarchy with actionable messages
4. **Configuration:** Environment variable support with validation
5. **User Experience:** Progress bars, better formatting, database info display
6. **RAG Quality:** Improved prompts with citations and factual instructions
7. **Performance:** Batch database operations, duplicate detection
8. **Testability:** Dependency injection, unit tests, no global state
9. **Documentation:** Type hints, docstrings, comprehensive error messages
10. **Web Interface:** Modern React frontend with FastAPI backend for better UX
11. **Deployment:** Production-ready Docker setup for easy deployment and demos
12. **Multi-Interface:** Both CLI and web UI supported from same codebase

## Docker Deployment

### Overview

A production-ready Docker setup for deploying the LAQ RAG system with minimal configuration. Designed for investor demos and production deployments on any machine with Docker installed.

**Key Design Decision:** Uses **host Ollama** instead of containerizing the LLM service to:
- Save ~4.5 GB image size
- Reduce startup time by 10+ minutes
- Leverage pre-downloaded models on demo machines
- Simplify deployment for presentations

### Architecture

**Three-Service Architecture:**
```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │─────▶│    Backend      │─────▶│   ChromaDB      │
│  (Nginx:80)     │      │  (FastAPI:8000) │      │  (Volume)       │
│  React SPA      │      │  Python 3.11    │      │  Vector Store   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Host Ollama    │
                         │  (Port 11434)   │
                         │  mistral +      │
                         │  nomic-embed    │
                         └─────────────────┘
```

**Service Details:**

1. **Frontend Container** (`frontend/Dockerfile`)
   - Multi-stage build: Node.js builder → Nginx server
   - Base image: `node:18-alpine` → `nginx:alpine`
   - Production Nginx with:
     - Gzip compression (level 6)
     - API proxy to backend at `/api`
     - Security headers (X-Frame-Options, X-Content-Type-Options)
     - Static asset caching (1 year for hashed files)
     - SPA routing fallback
   - Port: 80 (mapped to 3000 on host)
   - Size: ~25 MB

2. **Backend Container** (`backend/Dockerfile`)
   - Base image: `python:3.11-slim`
   - Ollama connection: `host.docker.internal:11434` (Windows/Mac compatible)
   - Health check: `/health` endpoint with 30s interval
   - Port: 8000
   - Volumes: `laq_chromadb:/app/laq_db` for persistent vector storage
   - Size: ~1.5 GB
   - Environment variables:
     - `OLLAMA_HOST=http://host.docker.internal:11434`
     - `DB_PATH=/app/laq_db`

3. **ChromaDB Storage**
   - Named volume: `laq_chromadb`
   - Mounted at: `/app/laq_db` in backend
   - Persists vector database across container restarts
   - Backup/restore commands in README.DOCKER.md

**Networking:**
- Custom bridge network: `laq_network`
- Frontend → Backend: `http://backend:8000`
- Backend → Ollama: `http://host.docker.internal:11434`

### Files Created

1. **`docker-compose.yml`** - Service orchestration
   - Defines 2 services (frontend, backend)
   - Named volume for ChromaDB persistence
   - Health checks and restart policies
   - Port mappings: 3000 (frontend), 8000 (backend)

2. **`backend/Dockerfile`** - Python backend image
   - Installs system dependencies for Docling
   - Copies requirements.txt and installs Python packages
   - Exposes port 8000
   - CMD: `uvicorn main:app --host 0.0.0.0 --port 8000`

3. **`frontend/Dockerfile`** - Multi-stage React build
   - Stage 1: Build React app with Vite
   - Stage 2: Serve static files with Nginx
   - Copies custom nginx.conf

4. **`frontend/nginx.conf`** - Production web server config
   - Reverse proxy for `/api/*` → `http://backend:8000`
   - Gzip compression for text assets
   - Cache control headers
   - SPA routing support
   - Security headers

5. **`backend/.dockerignore`** - Build optimization
   - Excludes: `venv/`, `__pycache__/`, `*.pyc`, `laq_db/`, `.env`

6. **`frontend/.dockerignore`** - Build optimization
   - Excludes: `node_modules/`, `dist/`, `.env`

7. **`README.DOCKER.md`** - Comprehensive Docker documentation (400+ lines)
   - Quick start guides (Windows/Linux/Mac)
   - Architecture diagrams
   - Troubleshooting scenarios
   - Volume management
   - Development workflows
   - Security best practices

### Deployment Workflow

**First-Time Setup:**
```bash
# 1. Ensure Ollama is running on host
ollama serve  # Should already be running
ollama pull mistral
ollama pull nomic-embed-text

# 2. Clone repository
git clone <repository-url>
cd minimal-local-RAG

# 3. Start all services
docker-compose up -d

# 4. Verify services
docker-compose ps
curl http://localhost:8000/health

# 5. Access application
# Open browser: http://localhost:3000
```

**Subsequent Starts:**
```bash
docker-compose up -d    # ~30 seconds
```

**Stopping:**
```bash
docker-compose down              # Stop containers, keep data
docker-compose down -v           # Stop containers, DELETE data
```

### Performance Characteristics

- **Image Sizes:**
  - Frontend: ~25 MB
  - Backend: ~1.5 GB
  - Total: ~1.5 GB (vs ~6 GB with containerized Ollama)

- **Startup Times:**
  - Cold start: 2-3 minutes (first time)
  - Warm start: ~30 seconds (subsequent)
  - Health check ready: ~10 seconds

- **Resource Usage:**
  - Memory: ~1-2 GB (containers only)
  - Ollama memory: ~4-8 GB (separate process)
  - Disk: ~1.5 GB images + database size

### Windows Docker Desktop Compatibility

The Docker setup is specifically designed for Windows Demo compatibility:

1. **Host Networking:**
   - Uses `host.docker.internal` instead of `localhost`
   - Works on Windows, macOS, and Linux (Docker 20.10+)

2. **Volume Mounts:**
   - Named volumes (not bind mounts) for cross-platform compatibility
   - No Windows path issues (`C:\` vs `/`)

3. **Line Endings:**
   - `.gitattributes` ensures LF in scripts
   - Nginx config uses Unix line endings

4. **Tested On:**
   - Docker Desktop for Windows
   - WSL2 backend recommended

### Common Operations

**View Logs:**
```bash
docker-compose logs -f backend    # Backend logs
docker-compose logs -f frontend   # Nginx access logs
docker-compose logs -f            # All services
```

**Rebuild After Code Changes:**
```bash
docker-compose up -d --build backend    # Rebuild backend only
docker-compose up -d --build            # Rebuild all
```

**Database Backup:**
```bash
docker run --rm -v laq_chromadb:/data -v $(pwd):/backup \
  alpine tar czf /backup/chromadb-backup.tar.gz -C /data .
```

**Database Restore:**
```bash
docker run --rm -v laq_chromadb:/data -v $(pwd):/backup \
  alpine tar xzf /backup/chromadb-backup.tar.gz -C /data
```

**Access Backend Shell:**
```bash
docker-compose exec backend bash
```

### Troubleshooting

See `README.DOCKER.md` for comprehensive troubleshooting guide covering:

1. **Ollama Connection Issues** - Backend can't reach host Ollama
2. **Port Conflicts** - Ports 3000/8000 already in use
3. **Model Not Found** - Mistral/nomic-embed-text not pulled
4. **Permission Errors** - Volume mount permission issues
5. **Build Failures** - Missing dependencies or network issues
6. **Slow Performance** - Resource allocation problems
7. **Frontend Can't Reach Backend** - Network configuration issues

### Development Mode

For development with hot-reload:

```bash
# Backend development
cd backend
docker-compose up -d chromadb    # Only run ChromaDB
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend development (separate terminal)
cd frontend
npm install
npm run dev    # Vite dev server with HMR
```

### Security Considerations

**Production Deployment Checklist:**
- [ ] Change default ports (not 3000/8000)
- [ ] Add TLS/SSL certificates to Nginx
- [ ] Set `CORS_ORIGINS` environment variable
- [ ] Enable rate limiting in FastAPI
- [ ] Use secrets management for sensitive configs
- [ ] Run containers as non-root user
- [ ] Enable Docker Content Trust
- [ ] Regular security updates for base images

**Current Security Features:**
- No hardcoded credentials
- Security headers in Nginx (X-Frame-Options, etc.)
- CORS configured in FastAPI backend
- Health check endpoints for monitoring
- Minimal base images (alpine/slim variants)

### Demo Day Checklist

Before presenting to investors:

1. **Pre-Demo (1 day before):**
   - [ ] Test `git clone` deployment on demo machine
   - [ ] Verify Ollama + models installed
   - [ ] Run `docker-compose up -d` and test all features
   - [ ] Prepare sample LAQ PDFs
   - [ ] Test search and chat with realistic queries

2. **Morning of Demo:**
   - [ ] Start Ollama: `ollama serve`
   - [ ] Start application: `docker-compose up -d`
   - [ ] Verify health: `curl http://localhost:8000/health`
   - [ ] Open browser tab: `http://localhost:3000`
   - [ ] Upload 2-3 LAQs to populate database

3. **Backup Plan:**
   - [ ] Have README.DOCKER.md open for troubleshooting
   - [ ] Know how to view logs: `docker-compose logs -f`
   - [ ] Alternative: Native setup if Docker fails

### Future Enhancements

Potential Docker improvements (not yet implemented):

1. **Ollama Container:** Add optional Ollama service to docker-compose.yml
2. **GPU Support:** Add NVIDIA runtime for GPU acceleration
3. **Scaling:** Add load balancer for multiple backend replicas
4. **Monitoring:** Add Prometheus + Grafana for metrics
5. **CI/CD:** Automated builds and tests in GitHub Actions
6. **Registry:** Push images to Docker Hub or private registry

## Development Considerations

- ChromaDB persistence ensures data survives application restarts
- Markdown truncated to configurable limit (default: 10,000 chars) to avoid token limits
- Ollama must be running locally before starting the application (host or container)
- No external API calls or internet connectivity required
- All configuration is centralized in `config.py` and can be overridden via `.env`
- Tests require Ollama to be running for integration tests (can be skipped)
- Docker deployment uses host Ollama by default (see Docker Deployment section)
