#!/bin/bash
# Chat APIをテストするためのcurlコマンド集

API_ENDPOINT="https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod"

echo "=== Chat API Test Script ==="
echo ""

# 1. POST /api/v1/chat/message - チャットメッセージ送信
echo "1. Sending chat message..."
curl -X POST "${API_ENDPOINT}/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "こんにちは",
    "session_id": "test-session-123"
  }' \
  -w "\n\nHTTP Status: %{http_code}\n" \
  | jq '.' 2>/dev/null || cat

echo ""
echo "---"
echo ""

# 2. POST /api/v1/chat/message - 別のメッセージ
echo "2. Sending another chat message..."
curl -X POST "${API_ENDPOINT}/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "日本語を学びたい",
    "session_id": "test-session-123"
  }' \
  -w "\n\nHTTP Status: %{http_code}\n" \
  | jq '.' 2>/dev/null || cat

echo ""
echo "---"
echo ""

# 3. GET /api/v1/chat - ルートパス（存在しないエンドポイントの可能性）
echo "3. Testing GET /api/v1/chat..."
curl -X GET "${API_ENDPOINT}/api/v1/chat" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  | jq '.' 2>/dev/null || cat

echo ""
echo "=== Test Complete ==="

