# Quick Setup Guide

## Prerequisites
- Docker Desktop (Windows/Mac/Linux)
- Git
- 8GB+ RAM
- 10GB+ disk space

## Installation Steps

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd indian-sme-doc-intelligence-rag
```

### 2. Configure Environment
```bash
cd backend
copy .env.example .env
# Edit .env if needed (defaults work for local development)
```

### 3. Deploy with Docker Compose
```bash
cd ..
docker-compose up --build
```

**First run only**: Ollama will download the Llama 3.3 8B model (~4.7GB). This takes 5-10 minutes depending on internet speed.

### 4. Access Applications
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/api/docs
- **Backend Health Check**: http://localhost:8000/api/health

### 5. Login
**Default Admin Account**:
- Email: `admin@demo.com`
- Password: `Admin@123`

**Or create a new account** at http://localhost:3000/register

## Development (Without Docker)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

### Port Already in Use
If ports 3000, 8000, 5432, or 11434 are in use:
1. Edit `docker-compose.yml` and change the port mappings
2. Or stop the conflicting services

### Ollama Model Download Fails
```bash
# Manual model download
docker exec -it rag-ollama ollama pull llama3.3:8b
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# View logs
docker logs rag-postgres
```

### Reset Everything
```bash
docker-compose down -v  # Removes all volumes
docker-compose up --build
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Build
```bash
cd frontend
npm run build
```

## Next Steps

1. Upload a sample GST invoice PDF
2. Wait for processing (status changes to "ready")
3. Start chatting with your document
4. Check admin dashboard for metrics

## Need Help?

- Check the full README.md for detailed documentation
- Open an issue on GitHub
- Review API docs at http://localhost:8000/api/docs
