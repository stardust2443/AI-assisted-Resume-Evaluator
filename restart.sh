#!/bin/bash
# restart.sh — Restart the AI Resume Evaluator (backend + public tunnel)
# Usage: bash restart.sh
# Tip: run after changing .env, after tunnel URL expires (~2 hrs), or after reboot

set -e
cd "$(dirname "$0")"

echo "🛑 Stopping old processes..."
pkill -f "uvicorn api.main" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 2

echo "⚙️  Starting FastAPI backend (port 8000)..."
python3 -W ignore -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 4

# Quick health check
if curl -sf http://localhost:8000/health >/dev/null; then
  echo "✅ Backend healthy (PID $BACKEND_PID)"
else
  echo "❌ Backend failed to start — check .env for GEMINI_API_KEY"
  exit 1
fi

echo ""
echo "🌐 Starting Cloudflare tunnel..."
/tmp/cloudflared tunnel --url http://localhost:8000 2>&1 &
TUNNEL_PID=$!
sleep 8

# Extract and print the public URL
URL=$(pgrep -a cloudflared 2>/dev/null || true)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ App is LIVE — check terminal output above for URL"
echo "  (look for: 'Your quick Tunnel has been created!'    )"
echo "  URL format: https://xxxxx.trycloudflare.com         "
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Backend PID : $BACKEND_PID"
echo "  Tunnel  PID : $TUNNEL_PID"
echo ""
echo "  To stop everything: pkill -f uvicorn; pkill -f cloudflared"
echo "  To change API key : edit .env then run this script again"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Keep script alive so tunnel stays up (Ctrl+C to stop)
wait $TUNNEL_PID
