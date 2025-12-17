#!/bin/bash
# Chat APIをローカルで起動するスクリプト

set -e

# 環境変数の設定
export PYTHONPATH="/Users/mo/Projects/japanese-learn-api/app/api/v1:$PYTHONPATH"

# .envファイルから環境変数を読み込む
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 必要な環境変数の確認
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEYが設定されていません"
    exit 1
fi

# デフォルト値の設定
export DYNAMODB_TABLE_NAME="${DYNAMODB_TABLE_NAME:-japanese-learn-table}"
export S3_BUCKET_NAME="${S3_BUCKET_NAME:-bucket-japanese-learn-resource}"
export FAISS_INDEX_S3_BUCKET_NAME="${FAISS_INDEX_S3_BUCKET_NAME:-japanese-learn-embeddings-index}"
export FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-https://nihongo.cloud}"
export CONVERSATION_LOGS_TABLE_NAME="${CONVERSATION_LOGS_TABLE_NAME:-japanese-learn-chat-conversations}"
export AWS_REGION="${AWS_REGION:-ap-northeast-1}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "=========================================="
echo "Chat API ローカル起動"
echo "=========================================="
echo "PYTHONPATH: $PYTHONPATH"
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "DYNAMODB_TABLE_NAME: $DYNAMODB_TABLE_NAME"
echo "S3_BUCKET_NAME: $S3_BUCKET_NAME"
echo "FAISS_INDEX_S3_BUCKET_NAME: $FAISS_INDEX_S3_BUCKET_NAME"
echo "AWS_REGION: $AWS_REGION"
echo "=========================================="
echo ""
echo "サーバーを起動しています..."
echo "http://localhost:8000 でアクセスできます"
echo "APIドキュメント: http://localhost:8000/docs"
echo ""
echo "テストコマンド例:"
echo "  curl -X POST http://localhost:8000/api/v1/chat/message \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"こんにちわ\", \"session_id\": \"test-123\"}'"
echo ""
echo "停止するには Ctrl+C を押してください"
echo ""

# 仮想環境をアクティベート（存在する場合）
if [ -f "$(dirname "$0")/../venv/bin/activate" ]; then
    source "$(dirname "$0")/../venv/bin/activate"
elif [ -f "$(dirname "$0")/../.venv/bin/activate" ]; then
    source "$(dirname "$0")/../.venv/bin/activate"
fi

# chatディレクトリに移動
cd "$(dirname "$0")/../app/api/v1/chat"

# uvicornで起動
uvicorn app:app --reload --port 8000 --host 0.0.0.0

