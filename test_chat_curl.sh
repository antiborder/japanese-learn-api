#!/bin/bash

# Chat API テスト用のcurlコマンド集
# ローカルサーバーが http://127.0.0.1:8000 で起動していることを前提

BASE_URL="http://127.0.0.1:8000/api/v1/chat"

echo "=== テスト1: 完全一致する単語の検索 ==="
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does こんにちは mean?",
    "session_id": "test-session-1"
  }' | jq '.'

echo -e "\n\n=== テスト2: スペルが少し違う単語の検索（意味検索のテスト） ==="
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does konnichiwa mean?",
    "session_id": "test-session-2"
  }' | jq '.'

echo -e "\n\n=== テスト3: 英語の意味から単語を検索（意味検索のテスト） ==="
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the Japanese word for hello?",
    "session_id": "test-session-3"
  }' | jq '.'

echo -e "\n\n=== テスト4: 漢字の意味から検索（意味検索のテスト） ==="
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the kanji for water?",
    "session_id": "test-session-4"
  }' | jq '.'

echo -e "\n\n=== テスト5: 漢字の読みから検索（意味検索のテスト） ==="
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about the kanji that means mountain",
    "session_id": "test-session-5"
  }' | jq '.'

echo -e "\n\n=== テスト6: 部分的な単語検索（意味検索のテスト） ==="
curl -X POST "${BASE_URL}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does arigato mean?",
    "session_id": "test-session-6"
  }' | jq '.'

