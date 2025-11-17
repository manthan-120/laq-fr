# Docker Deployment Guide - LAQ RAG System

Complete guide for running the LAQ RAG System using Docker containers. Perfect for demos, production deployments, and ensuring consistent environments across different machines.

## 📋 Prerequisites

### Required Software
1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
   - Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Minimum version: Docker 20.10+, Docker Compose 2.0+

2. **Ollama** (installed on host machine)
   - Download from: https://ollama.ai
   - Must have models pre-installed:
     ```bash
     ollama pull mistral
     ollama pull nomic-embed-text
     ```

3. **Git** (for cloning the repository)

### Verify Prerequisites
```bash
# Check Docker
docker --version          # Should be 20.10+
docker-compose --version  # Should be 2.0+

# Check Ollama (must be running)
ollama list              # Should show mistral and nomic-embed-text

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

---

## 🚀 Quick Start (Demo Day)

### On Windows Demo Machine

1. **Ensure Ollama is running**
   ```powershell
   # Check if Ollama is running
   ollama list

   # If not running, start it
   # Ollama should auto-start with Docker Desktop
   ```

2. **Clone the repository**
   ```powershell
   git clone https://github.com/your-username/minimal-local-RAG.git
   cd minimal-local-RAG
   ```

3. **Start all services**
   ```powershell
   docker-compose up -d
   ```

4. **Wait for services to be ready** (~30-60 seconds)
   ```powershell
   # Check service health
   docker-compose ps

   # View logs if needed
   docker-compose logs -f
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs

### On Linux/Mac

Same steps, but use `bash` instead of PowerShell:

```bash
# 1. Ensure Ollama is running
ollama serve &

# 2-5. Same commands as Windows
git clone https://github.com/your-username/minimal-local-RAG.git
cd minimal-local-RAG
docker-compose up -d
```

---

## 🏗️ Architecture

### Services Overview

```
┌─────────────────────────────────────────────┐
│         Browser (localhost:5173)            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Frontend       │  Nginx serving React
         │  (Port 80)      │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Backend        │  FastAPI application
         │  (Port 8000)    │
         └────┬─────┬──────┘
              │     │
       ┌──────┘     └──────────┐
       ▼                       ▼
┌─────────────┐      ┌──────────────────┐
│  ChromaDB   │      │  Ollama          │
│  (Volume)   │      │  (Host:11434)    │
└─────────────┘      └──────────────────┘
```

### Key Features

1. **Frontend Container**
   - Multi-stage build (Node builder + Nginx server)
   - Optimized production assets
   - Gzip compression enabled
   - Reverse proxy to backend API

2. **Backend Container**
   - Python 3.11 slim image
   - FastAPI with uvicorn
   - Connects to host Ollama via `host.docker.internal`
   - Health checks enabled

3. **Data Persistence**
   - ChromaDB data stored in Docker volume `laq-rag-chromadb`
   - Survives container restarts
   - Easy backup/restore

4. **Networking**
   - Custom bridge network for inter-container communication
   - Host network access for Ollama connection
   - Port mappings: 5173 (frontend), 8000 (backend)

---

## 📖 Detailed Usage

### Starting Services

```bash
# Start in detached mode (background)
docker-compose up -d

# Start with live logs
docker-compose up

# Start specific service
docker-compose up -d backend
```

### Stopping Services

```bash
# Stop all services (keeps data)
docker-compose down

# Stop and remove volumes (DELETES DATABASE!)
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 50 lines
docker-compose logs --tail=50 frontend

# Since specific time
docker-compose logs --since 2024-01-01T10:00:00
```

### Service Status

```bash
# Check service status
docker-compose ps

# Check health
docker-compose ps | grep healthy

# Detailed inspection
docker inspect laq-rag-backend
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend

# Rebuild and restart
docker-compose up -d --build
```

---

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  # Ollama settings
  - OLLAMA_BASE_URL=http://host.docker.internal:11434
  - LLM_MODEL=mistral
  - EMBEDDING_MODEL=nomic-embed-text

  # RAG settings
  - TOP_K=5
  - SIMILARITY_THRESHOLD=0.6
  - TEMPERATURE=0.1
```

### Port Customization

Change exposed ports in `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Change 5173 to 8080

  backend:
    ports:
      - "9000:8000"  # Change 8000 to 9000
```

### Volume Backup

```bash
# Backup ChromaDB data
docker run --rm \
  -v laq-rag-chromadb:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/chromadb-backup.tar.gz -C /source .

# Restore ChromaDB data
docker run --rm \
  -v laq-rag-chromadb:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/chromadb-backup.tar.gz -C /target
```

---

## 🐛 Troubleshooting

### Issue: Cannot connect to Ollama

**Symptoms:**
```
EmbeddingError: Cannot connect to Ollama at http://host.docker.internal:11434
```

**Solutions:**
1. Ensure Ollama is running on host:
   ```bash
   ollama list  # Should show models
   ```

2. On Linux, replace `host.docker.internal` with your local IP:
   ```bash
   # Find your IP
   ip addr show | grep inet

   # Update docker-compose.yml
   - OLLAMA_BASE_URL=http://192.168.1.100:11434
   ```

3. Check Ollama is listening on all interfaces:
   ```bash
   # Set OLLAMA_HOST environment variable
   export OLLAMA_HOST=0.0.0.0:11434
   ollama serve
   ```

---

### Issue: Models not found

**Symptoms:**
```
OllamaModelNotFoundError: Model 'mistral' not found
```

**Solution:**
```bash
# Pull required models on host
ollama pull mistral
ollama pull nomic-embed-text

# Verify
ollama list
```

---

### Issue: Port already in use

**Symptoms:**
```
Error: Bind for 0.0.0.0:5173 failed: port is already allocated
```

**Solution:**
```bash
# Find what's using the port
# Windows:
netstat -ano | findstr :5173

# Linux/Mac:
lsof -i :5173

# Option 1: Kill the process
# Option 2: Change port in docker-compose.yml
ports:
  - "5174:80"  # Use 5174 instead
```

---

### Issue: Frontend shows "Cannot connect to backend"

**Symptoms:**
- Frontend loads but API calls fail
- Network errors in browser console

**Solutions:**
1. Check backend is healthy:
   ```bash
   docker-compose ps
   curl http://localhost:8000/api/health
   ```

2. Check Nginx proxy configuration:
   ```bash
   docker-compose logs frontend | grep error
   ```

3. Verify services are on same network:
   ```bash
   docker network inspect laq-rag-network
   ```

---

### Issue: Slow first startup

**Explanation:**
- First build downloads base images (~1GB)
- Installs all dependencies
- Expected: 3-5 minutes on fast internet

**Optimization:**
```bash
# Pre-pull base images
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull nginx:alpine

# Then build
docker-compose build
```

---

### Issue: Windows line ending errors

**Symptoms:**
```
/bin/sh: syntax error: unexpected end of file
```

**Solution:**
```bash
# Convert line endings
git config --global core.autocrlf false
git rm --cached -r .
git reset --hard
```

---

## 📊 Performance Optimization

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          memory: 2G
```

### Build Cache Optimization

```bash
# Build with no cache
docker-compose build --no-cache

# Pull latest base images
docker-compose build --pull

# Parallel builds
docker-compose build --parallel
```

---

## 🔒 Security Considerations

### Production Checklist

- [ ] Change default ports
- [ ] Set proper CORS origins in backend
- [ ] Use environment files for secrets (not hardcoded)
- [ ] Enable HTTPS (add reverse proxy like Traefik)
- [ ] Limit container resources
- [ ] Regular security updates: `docker-compose pull`
- [ ] Use Docker secrets for sensitive data
- [ ] Scan images: `docker scan laq-rag-backend`

---

## 📚 Advanced Usage

### Development Mode with Hot Reload

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - ./backend:/app  # Mount source code
    command: uvicorn app.main:app --reload --host 0.0.0.0

  frontend:
    build:
      context: ./frontend
      target: builder  # Stop at build stage
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev
    ports:
      - "5173:5173"
```

Run: `docker-compose -f docker-compose.dev.yml up`

---

### Multi-Environment Setup

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

# Testing
docker-compose -f docker-compose.yml -f docker-compose.test.yml run tests
```

---

### Scaling Services

```bash
# Run 3 backend instances (requires load balancer)
docker-compose up -d --scale backend=3

# Note: Requires removing container_name and adding load balancer
```

---

## 📈 Monitoring

### Health Checks

```bash
# Check health status
docker-compose ps

# Manual health check
curl http://localhost:8000/api/health
curl http://localhost:5173/health
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Container sizes
docker-compose images

# Disk usage
docker system df
```

---

## 🧹 Cleanup

### Remove Everything

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (DELETES DATA!)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Remove orphaned containers
docker-compose down --remove-orphans

# Full cleanup (all Docker resources)
docker system prune -a --volumes
```

### Selective Cleanup

```bash
# Remove only stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune
```

---

## 🎯 Demo Day Checklist

### Before Demo

- [ ] Test on demo machine beforehand
- [ ] Ensure Docker Desktop is installed
- [ ] Verify Ollama is installed with models
- [ ] Clone repository
- [ ] Test `docker-compose up -d`
- [ ] Verify http://localhost:5173 loads
- [ ] Prepare sample PDFs in `sample_pdfs/`
- [ ] Test upload, search, and chat flows

### During Demo

1. Open terminal in project directory
2. Run: `docker-compose up -d`
3. Wait 30-60 seconds
4. Open: http://localhost:5173
5. Demonstrate features

### After Demo

```bash
# Stop services (keeps data)
docker-compose down

# Or remove everything
docker-compose down -v
```

---

## 🆘 Getting Help

### Useful Commands

```bash
# Full service information
docker-compose config

# Validate compose file
docker-compose config --quiet

# List all containers
docker ps -a

# List all volumes
docker volume ls

# Network information
docker network ls
```

### Log Collection

```bash
# Collect all logs for debugging
docker-compose logs > debug-logs.txt

# System information
docker version > system-info.txt
docker-compose version >> system-info.txt
```

---

## 📝 Notes

- **First startup**: 2-5 minutes (downloading images, building)
- **Subsequent startups**: 30-60 seconds
- **Disk usage**: ~1.5 GB (images) + database size
- **Memory usage**: ~1-2 GB (all services)
- **Windows compatibility**: Tested on Docker Desktop for Windows
- **Mac compatibility**: Tested on Docker Desktop for Mac
- **Linux compatibility**: Tested on Ubuntu 22.04 with Docker Engine

---

## 🔗 Related Documentation

- Main README: [README.md](README.md)
- Development Guide: [docs/CLAUDE.md](docs/CLAUDE.md)
- API Documentation: http://localhost:8000/api/docs (when running)
- Docker Documentation: https://docs.docker.com
- Docker Compose Reference: https://docs.docker.com/compose/compose-file

---

**Built with Docker for consistent, reproducible deployments across all environments.**
