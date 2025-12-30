#!/bin/bash
# Start script for Tatort on the Road API

set -e

echo "🎬 Tatort on the Road - API Server Startup"
echo "=========================================="

# Check if running in Docker or locally
if [ -f "/.dockerenv" ]; then
    echo "✓ Running in Docker container"
    API_URL="http://tatort-api:8000"
else
    echo "✓ Running locally"
    API_URL="http://localhost:8000"
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.10+"
    exit 1
fi

echo "✓ Python found: $(python --version)"

# Check if requirements are installed
echo "📦 Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✓ Dependencies already installed"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads output

echo ""
echo "🚀 Starting API server..."
echo "📍 API will be available at: $API_URL"
echo "📚 API docs at: $API_URL/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python -m uvicorn app.api_server:app --host 0.0.0.0 --port 8000 --reload
