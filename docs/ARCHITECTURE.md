# Architecture Overview

## System Design Principles

LAQ RAG follows enterprise-grade architectural patterns with a focus on modularity, scalability, and maintainability.

### Core Principles
- **Separation of Concerns**: Clear boundaries between frontend, backend, and data layers
- **Single Responsibility**: Each module has one primary function
- **Dependency Injection**: Configuration-driven behavior with environment variables
- **Error Boundaries**: Comprehensive error handling and graceful degradation
- **Security by Default**: No hardcoded secrets, input validation, CORS policies

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • API Endpoints │    │ • Ollama LLM    │
│ • Search UI     │    │ • Business Logic│    │ • ChromaDB      │
│ • Chat Interface│    │ • Data Processing│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Data Layer    │
                       │                 │
                       │ • Vector DB     │
                       │ • File Storage  │
                       │ • Cache         │
                       └─────────────────┘
```

## Backend Architecture

### Layered Architecture Pattern

```
app/
├── api/           # Presentation Layer
│   └── endpoints/ # REST API endpoints
├── core/          # Configuration Layer
├── models/        # Domain Models (Pydantic)
├── services/      # Business Logic Layer
│   ├── config.py
│   ├── database.py
│   ├── embeddings.py
│   ├── pdf_processor.py
│   └── rag.py
└── main.py        # Application Entry Point
```

### Service Layer Responsibilities

- **Config Service**: Environment variable management, validation
- **Database Service**: ChromaDB vector operations, CRUD operations
- **Embeddings Service**: Text vectorization using Ollama
- **PDF Processor**: Document parsing, LLM extraction, data validation
- **RAG Service**: Query processing, similarity search, response generation

## Data Flow

### PDF Processing Pipeline

1. **Upload**: PDF file received via REST API
2. **Validation**: File type, size, and integrity checks
3. **Extraction**: Docling converts PDF to structured markdown
4. **LLM Processing**: Mistral extracts Q&A pairs from markdown
5. **Vectorization**: nomic-embed-text generates embeddings
6. **Storage**: Q&A pairs and vectors stored in ChromaDB
7. **Indexing**: Metadata indexed for efficient retrieval

### Query Processing Flow

1. **Query Reception**: Natural language query via API
2. **Embedding**: Query converted to vector representation
3. **Similarity Search**: Cosine similarity against stored vectors
4. **Retrieval**: Top-k most similar Q&A pairs fetched
5. **Ranking**: Results filtered by similarity threshold
6. **Response**: Formatted results returned to frontend

## Frontend Architecture

### Component Architecture

```
src/
├── components/     # Reusable UI components
│   ├── layout/    # Layout components (Header, Sidebar)
│   └── common/    # Shared components
├── pages/         # Page-level components
├── services/      # API integration layer
└── styles/        # Global styles and design tokens
```

### State Management

- **Local State**: React hooks for component-level state
- **API State**: Direct API calls with error handling
- **No Global State**: Simple architecture without Redux/Zustand

## Security Architecture

### Authentication & Authorization
- **CORS Policy**: Configured origins for frontend-backend communication
- **Input Validation**: Pydantic models for request/response validation
- **Environment Variables**: Sensitive configuration via .env files

### Data Protection
- **Local Processing**: All data processing occurs offline
- **No External APIs**: Self-contained system with local dependencies
- **File Validation**: Strict PDF validation and size limits

## Deployment Architecture

### Containerized Deployment

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │
│   Container     │    │   Container     │
│                 │    │                 │
│ • Nginx         │    │ • FastAPI       │
│ • Static Files  │    │ • Python App    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                 │
         ┌─────────────────┐
         │   Docker        │
         │   Compose       │
         │                 │
         │ • Networking    │
         │ • Volumes       │
         │ • Environment   │
         └─────────────────┘
```

### Local Dependencies

- **Ollama**: Runs as host service, accessed via HTTP API
- **ChromaDB**: Persistent vector database with file-based storage
- **Cache**: Local filesystem caching for processed documents

## Performance Considerations

### Optimization Strategies
- **Async Processing**: FastAPI async endpoints for concurrent requests
- **Caching**: Markdown conversion and embedding results cached
- **Batch Processing**: Vector operations optimized for batch sizes
- **Lazy Loading**: Frontend components loaded on demand

### Scalability Patterns
- **Horizontal Scaling**: Multiple backend instances behind load balancer
- **Database Sharding**: ChromaDB supports collection-based partitioning
- **CDN Integration**: Static assets served via CDN in production

## Monitoring & Observability

### Health Checks
- **Application Health**: `/api/health` endpoint with dependency checks
- **Dependency Monitoring**: Ollama and database connectivity validation
- **Performance Metrics**: Response times and error rates tracking

### Logging Strategy
- **Structured Logging**: JSON format with log levels
- **Error Tracking**: Comprehensive exception handling with context
- **Audit Trail**: API request/response logging for debugging

## Future Architecture Evolution

### Planned Enhancements
- **Microservices**: Split monolithic backend into domain services
- **Event-Driven**: Asynchronous processing with message queues
- **Multi-Model**: Support for additional LLM providers
- **Distributed Storage**: Cloud-native vector database integration
