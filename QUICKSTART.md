# Quick Start Guide

Get the Graph Query System running in 5 minutes.

## 1. Get API Key (1 minute)

1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy your key

## 2. Setup Backend (2 minutes)

```bash
cd backend

# Create .env file
cp .env.example .env

# Edit .env and paste your API key:
# GEMINI_API_KEY=your_key_here
# DATABASE_URL=postgresql://localhost:5432/graph_query_db
```

On macOS/Linux:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Load sample data
python ingest.py

# Start server
python main.py
```

**Server runs on http://localhost:8000**

## 3. Setup Frontend (1 minute)

In another terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Frontend runs on http://localhost:5173**

## 4. Test It (1 minute)

1. Open http://localhost:5173
2. Enter query: "Trace order #1"
3. Click submit
4. View flow visualization

Done!

---

## Quick Query Examples

```
"Show all orders"
"Trace order #2"
"How many customers?"
"List invoices"
```

---

## Using Docker (Even Simpler)

```bash
# Copy API key to backend/.env
cp backend/.env.example backend/.env
# Edit backend/.env and add GEMINI_API_KEY

# Start everything
docker-compose up -d

# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

---

## Database Setup

### PostgreSQL (Recommended)

**macOS**:
```bash
brew install postgresql
brew services start postgresql
createdb graph_query_db
```

**Linux**:
```bash
sudo apt-get install postgresql
sudo systemctl start postgresql
sudo -u postgres createdb graph_query_db
```

**Windows**:
- Download from postgresql.org
- Install and note password
- Update DATABASE_URL in .env

### Or Use SQLite (Development)

Change in `backend/.env`:
```
DATABASE_URL=sqlite:///./graph_query.db
```

---

## Troubleshooting

### Backend won't start

```bash
# Check port 8000 is free
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Try different port
PORT=8001 python main.py
```

### "Cannot connect to database"

```bash
# Check PostgreSQL is running
psql -U postgres

# Or use SQLite instead (see above)
```

### "GEMINI_API_KEY not set"

```bash
# Verify .env file exists
cat backend/.env

# Check API key is set
echo $GEMINI_API_KEY
```

### Frontend can't reach backend

```bash
# Check VITE_API_URL in frontend/.env
cat frontend/.env

# Should be: http://localhost:8000

# Check backend is running
curl http://localhost:8000/health
```

---

## Next Steps

After it's running:

1. **Read Documentation**
   - README.md for overview
   - ARCHITECTURE.md for design details

2. **Explore Features**
   - Try different queries
   - Trace entities through flow
   - Check API documentation at /docs

3. **Review Code**
   - backend/query_engine/pipeline.py (core logic)
   - backend/query_engine/validator.py (safety)
   - frontend/src/App.jsx (React structure)

4. **Run Tests**
   - See TESTING.md for test scenarios
   - Try the example queries listed

---

## One-Command Start (Unix Only)

```bash
chmod +x start.sh
./start.sh
```

This starts both backend and frontend automatically.

---

## That's It!

You're all set. Happy querying!

For more details, see SETUP.md or README.md
