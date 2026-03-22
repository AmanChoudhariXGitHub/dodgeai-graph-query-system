#!/bin/bash

# Graph Query System - Startup Script

set -e

echo "🚀 Starting Graph Query System..."

# Backend setup
echo ""
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found in backend directory"
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Please edit backend/.env with your configuration:"
    echo "  - DATABASE_URL: PostgreSQL connection string"
    echo "  - GEMINI_API_KEY: From https://aistudio.google.com/apikey"
fi

# Initialize database
echo "Initializing database..."
python ingest.py

# Start backend
echo ""
echo "✅ Backend ready!"
echo "Starting FastAPI server on http://localhost:8000..."
python main.py &
BACKEND_PID=$!

# Frontend setup
echo ""
echo "📦 Setting up frontend..."
cd ../frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install -q
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
fi

# Start frontend
echo ""
echo "✅ Frontend ready!"
echo "Starting Vite dev server on http://localhost:5173..."
npm run dev &
FRONTEND_PID=$!

# Show startup complete
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║   ✅ Graph Query System is running!                ║"
echo "╠════════════════════════════════════════════════════╣"
echo "║   Backend:  http://localhost:8000                  ║"
echo "║   Frontend: http://localhost:5173                  ║"
echo "║   API Docs: http://localhost:8000/docs             ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait
