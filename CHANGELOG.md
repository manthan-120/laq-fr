# Changelog

All notable changes to LAQ RAG will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- SECURITY.md with vulnerability reporting guidelines
- ARCHITECTURE.md with comprehensive system design documentation
- CONTRIBUTING.md with development and contribution guidelines
- Enhanced health check endpoint with Ollama connectivity validation

### Changed
- Professional README.md rewrite with problem/solution focus
- Improved error handling in PDF processing pipeline

### Security
- Verified no hardcoded secrets in codebase
- Enhanced .gitignore for comprehensive coverage
- Updated python-multipart from 0.0.6 to 0.0.9 (fixes DoS vulnerabilities)
- Updated tqdm from 4.66.1 to 4.66.4 (fixes CLI argument vulnerability)

## [1.0.0] - 2025-12-29

### Added
- Initial release of LAQ RAG system
- PDF upload and processing with Docling
- LLM-powered Q&A extraction using Mistral
- Vector database integration with ChromaDB
- Semantic search with similarity scoring
- Modern React frontend with dark mode UI
- FastAPI backend with comprehensive API endpoints
- Docker containerization for easy deployment
- Comprehensive testing suite with pytest
- CI/CD pipeline with GitHub Actions

### Features
- Offline RAG system with no external API dependencies
- Legislative Assembly Question processing
- Natural language search interface
- Responsive web dashboard
- Database statistics and management
- PDF validation and error handling
- Caching system for performance optimization

### Technical
- Backend: FastAPI, Pydantic, ChromaDB, Ollama integration
- Frontend: React 18, Vite, Axios, Vanilla CSS
- Infrastructure: Docker, Docker Compose, Nginx
- Testing: pytest, coverage reporting
- Documentation: Comprehensive README and API docs

[Unreleased]: https://github.com/your-org/laq-rag/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-org/laq-rag/releases/tag/v1.0.0
