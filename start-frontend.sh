#!/bin/bash

# Start Frontend Script

echo "🚀 Starting AI Portfolio Frontend..."
echo "==================================="

cd frontend

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install --legacy-peer-deps
fi

# Start the development server
echo "🎯 Starting React development server..."
echo "📍 Frontend will be available at: http://localhost:3000"
echo ""
npm start


