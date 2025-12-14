#!/bin/bash

# デバッグ用スクリプト - ログを確認しながらテスト

BASE_URL="http://127.0.0.1:8000/api/v1/chat"

echo "=== デバッグ: ツール関数が呼ばれているか確認 ==="
echo "サーバーのログを確認してください（別ターミナルでuvicornが動いているはず）"
echo ""

echo "テスト1: 完全一致（日本語）"
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does こんにちは mean?",
    "session_id": "debug-1"
  }' | python3 -m json.tool

echo -e "\n\nテスト2: ローマ字（意味検索が必要）"
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does konnichiwa mean?",
    "session_id": "debug-2"
  }' | python3 -m json.tool

echo -e "\n\nテスト3: 英語から検索（意味検索が動作）"
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the Japanese word for hello?",
    "session_id": "debug-3"
  }' | python3 -m json.tool

echo -e "\n\n=== 確認ポイント ==="
echo "1. サーバーログで 'Tool calls made:' が表示されているか"
echo "2. サーバーログで 'Tool results:' が表示されているか"
echo "3. サーバーログで 'Could not initialize RAG service' などのエラーがないか"
echo "4. サーバーログで 'Found word via vector search' が表示されているか"

