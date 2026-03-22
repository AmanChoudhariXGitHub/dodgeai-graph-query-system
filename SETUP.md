# Setup Guide

Complete setup instructions for the Graph Query System.

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+ (or Docker)
- Google Gemini API key (free)

## Quick Start (Recommended)

### 1. Get API Key

1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy your key

### 2. Clone and Setup

```bash
# Clone repository
git clone <repo-url>
cd graph-query-system

# Make startup script executable
chmod +x start.sh

# Run startup script
./start.sh
```

The script will:
- Create Python virtual environment
- Install all dependencies
- Initialize the database with sample data
- Start both backend and frontend servers

Open http://localhost:5173 to use the system.

---

## Manual Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `backend/.env`:
```
DATABASE_URL=postgresql://localhost:5432/graph_query_db
GEMINI_API_KEY=your_key_here
PORT=8000
DEBUG=True
```

Initialize database:
```bash
python ingest.py
```

Start server:
```bash
python main.py
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
```

Edit `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

Start development server:
```bash
npm run dev
```

Frontend will be available at http://localhost:5173

---

## Database Setup

### Option 1: PostgreSQL (Recommended)

**macOS (with Homebrew):**
```bash
brew install postgresql
brew services start postgresql
createdb graph_query_db
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb graph_query_db
```

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- Install and remember the password
- Set DATABASE_URL in .env:
  ```
  DATABASE_URL=postgresql://postgres:password@localhost:5432/graph_query_db
  ```

**Docker:**
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=graph_query_db \
  -p 5432:5432 \
  postgres:15-alpine
```

### Option 2: SQLite (Development Only)

Change DATABASE_URL in `.env`:
```
DATABASE_URL=sqlite:///./graph_query.db
```

Then run:
```bash
python ingest.py
```

---

## Environment Variables

### Backend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `PORT` | No | Server port (default: 8000) |
| `DEBUG` | No | Enable debug mode (default: False) |

### Frontend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | No | Backend API URL (default: http://localhost:8000) |

---

## Docker Setup

### Using Docker Compose

```bash
# Create .env file with your Gemini API key
cp backend/.env.example backend/.env
# Edit backend/.env and add GEMINI_API_KEY

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432

### Using Docker Directly

```bash
# Build image
docker build -t graph-query-system .

# Run container
docker run -d \
  -e DATABASE_URL=postgresql://user:password@host:5432/db \
  -e GEMINI_API_KEY=your_key \
  -p 8000:8000 \
  -p 5173:5173 \
  graph-query-system
```

---

## Deployment

### Deploy to Render

#### Backend

1. Push code to GitHub
2. Go to https://render.com/dashboard
3. Click "New +" → "Web Service"
4. Connect GitHub repository
5. Configure:
   - **Name**: graph-query-backend
   - **Environment**: Python
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python main.py`
6. Add environment variables:
   - `DATABASE_URL`: Neon PostgreSQL URL
   - `GEMINI_API_KEY`: Your API key
7. Deploy

#### Frontend

1. Create new Web Service (same process)
2. Configure:
   - **Name**: graph-query-frontend
   - **Environment**: Node
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Start Command**: `cd frontend && npm run preview`
3. Add environment variable:
   - `VITE_API_URL`: Your Render backend URL
4. Deploy

### Deploy to Vercel

**Frontend:**
1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import GitHub repository
4. Set root directory: `frontend`
5. Add environment: `VITE_API_URL=your_backend_url`
6. Deploy

### Deploy to AWS

**Using CloudFormation** (template in `infra/` directory)

**Manual:**
1. RDS: Create PostgreSQL instance
2. Lambda/EC2: Deploy backend
3. S3 + CloudFront: Deploy frontend
4. API Gateway: Route requests

---

## Troubleshooting

### Backend won't start

```bash
# Check if port is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Try different port
PORT=8001 python main.py
```

### Database connection error

```bash
# Check PostgreSQL is running
psql -U postgres -d graph_query_db

# Test connection string
DATABASE_URL=postgresql://user:pass@localhost:5432/graph_query_db python ingest.py
```

### API key error

```bash
# Verify key format
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"

# Test API
python -c "import google.generativeai as genai; genai.configure(api_key='your_key')"
```

### Frontend can't reach API

```bash
# Check backend is running
curl http://localhost:8000/health

# Check VITE_API_URL is set
echo $VITE_API_URL

# Check proxy in vite.config.js
```

### Sample data not loading

```bash
# Verify database exists
psql -l

# Re-run ingest
python ingest.py

# Check logs
tail -f /var/log/postgresql/postgresql.log
```

---

## Development Workflow

### Running Tests

```bash
cd backend

# Run pytest
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Code Formatting

```bash
cd backend
black . --line-length=100
isort .

cd ../frontend
npm run format
```

### Linting

```bash
cd backend
flake8 .
mypy .

cd ../frontend
npm run lint
```

---

## Performance Optimization

### Backend

1. **Database Indexing** - Already configured in models.py
2. **Query Caching** - Implement Redis for frequent queries
3. **Connection Pooling** - SQLAlchemy handles this
4. **API Rate Limiting** - Use FastAPI middleware

### Frontend

1. **Code Splitting** - Vite handles automatically
2. **Image Optimization** - Use optimized formats
3. **Lazy Loading** - Implement for React Flow
4. **Caching** - Browser cache for API responses

---

## Monitoring & Logging

### Backend Logs

```bash
# View logs
tail -f backend.log

# Enable debug logging
DEBUG=True python main.py
```

### Frontend Logs

```bash
# Check browser console (F12)
# Check network tab for API calls
# Enable verbose logging in components
```

### Metrics

```bash
# Backend health
curl http://localhost:8000/health

# Query performance
# Check execution_time_ms in response
```

---

## Security Checklist

- [ ] Store API keys in environment variables (not in code)
- [ ] Use HTTPS in production
- [ ] Enable CORS only for trusted domains
- [ ] Use strong database passwords
- [ ] Enable query result limits
- [ ] Monitor API usage
- [ ] Keep dependencies updated
- [ ] Use secrets management service

---

## Next Steps

1. ✅ Complete setup
2. ✅ Load sample data
3. ✅ Test backend API: http://localhost:8000/docs
4. ✅ Test frontend: http://localhost:5173
5. ✅ Try example queries
6. ✅ Deploy to production

---

## Support

For issues:
1. Check error messages in frontend/browser console
2. Check backend logs: `tail -f backend.log`
3. Verify database connectivity: `psql -U postgres -d graph_query_db`
4. Test API with curl: `curl http://localhost:8000/api/schema`
5. Review README.md for architectural details
