#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ec2-user/ChatMRPT"
ENV_FILE="$APP_DIR/.env"

echo "Fixing OpenAI env at $(hostname)"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found" >&2
  exit 1
fi

cd "$APP_DIR"
backup=".env.backup_$(date +%Y%m%d_%H%M%S)"
cp .env "$backup"
echo "Backed up .env to $backup"

# Remove any incorrect OpenAI base URL overrides
sed -i '/^OPENAI_BASE_URL=/d' .env || true
sed -i '/^OPENAI_API_BASE=/d' .env || true

# Ensure model name and fallbacks
if grep -q '^OPENAI_MODEL_NAME=' .env; then
  sed -i 's/^OPENAI_MODEL_NAME=.*/OPENAI_MODEL_NAME=chatgpt-4o-latest/' .env
else
  echo 'OPENAI_MODEL_NAME=chatgpt-4o-latest' >> .env
fi

if grep -q '^OPENAI_MODEL_FALLBACKS=' .env; then
  sed -i 's/^OPENAI_MODEL_FALLBACKS=.*/OPENAI_MODEL_FALLBACKS=chatgpt-4o-latest,gpt-4o-mini/' .env
else
  echo 'OPENAI_MODEL_FALLBACKS=chatgpt-4o-latest,gpt-4o-mini' >> .env
fi

echo "Current OpenAI settings:"
grep -E '^OPENAI_' .env || true

echo "Restarting service..."
sudo systemctl restart chatmrpt || sudo systemctl restart gunicorn || sudo supervisorctl restart all || true

echo "Done."

