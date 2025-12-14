#!/bin/bash

# チャットAPIテスト用スクリプト（ログ確認用）
# サーバーログを確認しながらテスト

BASE_URL="http://127.0.0.1:8000/api/v1/chat"

echo "=== テスト: 意味検索（konnichiwa） ==="
echo "サーバーログを確認してください..."
echo ""

curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does konnichiwa mean?",
    "session_id": "test-semantic-search"
  }'

echo -e "\n\n=== 確認ポイント ==="
echo "サーバーログで以下を確認:"
echo "1. 'Initializing RAG service (first time)...' - RAG初期化"
echo "2. 'Loading FAISS index from S3...' - S3から読み込み"
echo "3. 'Tool calls made:' - ツール関数が呼ばれたか"
echo "4. 'Attempting vector search for word:' - ベクトル検索実行"
echo "5. 各処理の所要時間"

