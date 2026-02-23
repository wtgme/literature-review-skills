#!/usr/bin/env bash
# Daily AI paper digest — run by cron.
# Loads nvm, sources private env vars, then invokes the Gemini skill.

set -euo pipefail

# Load nvm so `gemini` is on PATH
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

# Load private env vars (DIGEST_EMAIL, GDRIVE_*, etc.)
# Create ~/.env.literature-review — never commit it.
ENV_FILE="$HOME/.env.literature-review"
if [ -f "$ENV_FILE" ]; then
  source "$ENV_FILE"
else
  echo "ERROR: $ENV_FILE not found." >&2
  exit 1
fi

# Run from project root so Gemini picks up .gemini/skills/
cd "$(dirname "$0")/.."

gemini --yolo -p "fetch-latest-ai-papers 1" \
  >> "$HOME/logs/literature-review-digest.log" 2>&1
