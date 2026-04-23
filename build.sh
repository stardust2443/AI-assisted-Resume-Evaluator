#!/bin/bash
# build.sh — Render.com build script
# Runs during every deployment: installs Python deps + builds React app
set -e  # Exit immediately on any error

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "⚛️  Building React frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✅ Build complete — React app is in frontend/dist/"
