#!/bin/bash

# Start Backend Script

echo "🚀 Starting AI Portfolio Backend..."
echo "=================================="

cd backend

# Check if virtual environment exists
if [ ! -d "portfolio" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv portfolio
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source portfolio/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env and add your API keys before continuing!"
    exit 1
fi

# Check if resume.pdf exists
if [ ! -f "data/resume.pdf" ]; then
    echo "⚠️  Warning: resume.pdf not found at backend/data/resume.pdf"
    echo "📄 Please add your resume PDF to continue!"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# Start the server
echo "🎯 Starting FastAPI server..."
echo "📍 Backend will be available at: http://localhost:8000"
echo "📖 API docs at: http://localhost:8000/docs"
echo ""
uvicorn server:app --reload --host 0.0.0.0 --port 8000


