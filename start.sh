#!/usr/bin/env bash
set -euo pipefail

# MindForge — start all three services
# Usage: ./start.sh

CYAN='\033[0;36m'
GREEN='\033[0;32m'
MAGENTA='\033[0;35m'
RESET='\033[0m'
BOLD='\033[1m'

PIDS=()

cleanup() {
  echo ""
  echo -e "${BOLD}Shutting down MindForge...${RESET}"
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null
  echo -e "${GREEN}All services stopped.${RESET}"
  exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${BOLD}Starting MindForge...${RESET}"
echo ""

# 1. Python AI Engine (port 8000)
echo -e "${CYAN}[engine]${RESET} Starting FastAPI on :8000..."
(cd ai-engine && source .venv/bin/activate && python -m app) &
PIDS+=($!)

# 2. Express Gateway (port 5000)
echo -e "${GREEN}[gateway]${RESET} Starting Express on :5000..."
(cd server-gateway && npm run dev) &
PIDS+=($!)

# 3. Vite Client (port 5173)
echo -e "${MAGENTA}[client]${RESET} Starting Vite on :5173..."
(npm run dev --prefix client) &
PIDS+=($!)

echo ""
echo -e "${BOLD}All services running:${RESET}"
echo -e "  ${CYAN}Engine${RESET}   → http://localhost:8000"
echo -e "  ${GREEN}Gateway${RESET}  → http://localhost:5000"
echo -e "  ${MAGENTA}Client${RESET}   → http://localhost:5173"
echo ""
echo -e "${BOLD}Press Ctrl+C to stop all services.${RESET}"
echo ""

wait
