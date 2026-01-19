#!/bin/bash
# Synchronize the compiled React bundle to a remote instance, removing stale hashed assets.

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <instance_ip> [ssh_key_path]"
  exit 1
fi

TARGET="$1"
KEY_PATH="${2:-~/.ssh/chatmrpt-key.pem}"

SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)/app/static/react/"
REMOTE_DIR="/home/ec2-user/ChatMRPT/app/static/react/"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "❌ Build output not found at $SOURCE_DIR"
  exit 1
fi

echo "📦 Syncing compiled frontend assets to $TARGET"
rsync -avz --delete \
  -e "ssh -i $KEY_PATH -o StrictHostKeyChecking=no" \
  "$SOURCE_DIR" \
  ec2-user@"$TARGET":"$REMOTE_DIR"

echo "✅ Frontend assets synchronized to $TARGET"
