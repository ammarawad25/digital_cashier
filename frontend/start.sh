#!/bin/bash

# Customer Service Agent Frontend - Quick Start Script
# This script sets up and runs the frontend in development mode

set -e  # Exit on error

echo "🚀 Customer Service Agent - Frontend Setup & Start"
echo "=================================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo ""

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "⚠️  package.json not found. Make sure you're in the frontend directory."
    echo "   Run: cd frontend"
    exit 1
fi

echo "📦 Installing dependencies..."
if npm install; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🎨 Building Tailwind CSS..."
npm run build:css 2>/dev/null || true

echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Make sure the backend API is running:"
echo "   cd ../src"
echo "   python -m uvicorn main:app --reload --port 8000"
echo ""
echo "2. In another terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open your browser:"
echo "   🌐 http://localhost:3000"
echo ""
echo "📚 Useful Commands:"
echo "   npm test              - Run unit tests"
echo "   npm test:ui           - Run tests with UI"
echo "   npm run test:e2e      - Run E2E tests"
echo "   npm run build         - Build for production"
echo ""
echo "📖 Documentation:"
echo "   README.md             - Project overview"
echo "   TESTING.md            - Testing guide"
echo "   DEPLOYMENT.md         - Deployment guide"
echo ""
echo "🎉 Happy coding!"
