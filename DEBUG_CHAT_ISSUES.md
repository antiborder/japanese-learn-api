# チャット意味検索のデバッグガイド

## 現在の問題

テスト結果から以下の問題が確認されています：

1. **テスト1（完全一致）**: `word_ids: null` - ツール関数が呼ばれていない可能性
2. **テスト2（ローマ字）**: 見つからない - 意味検索が動作していない
3. **テスト3（英語から検索）**: ✅ 成功 - `word_ids: [613]`
4. **テスト4（漢字の意味）**: 見つからない

## デバッグ手順

### 1. サーバーログを確認

uvicornが動いているターミナルで、以下のログを確認：

```
INFO: Tool calls made: [...]
INFO: Tool results: [...]
WARNING: Could not initialize RAG service: ...
INFO: Found word via vector search: ...
```

### 2. 考えられる原因

#### 原因1: RAGサービスが初期化されていない

**確認方法**:
- サーバーログに `Could not initialize RAG service` が表示されているか
- 環境変数が設定されているか（`S3_BUCKET_NAME`, `AWS_REGION`など）

**解決方法**:
```bash
# 環境変数を設定
export S3_BUCKET_NAME="your-bucket-name"
export AWS_REGION="ap-northeast-1"
export DYNAMODB_TABLE_NAME="japanese-learn-table"

# サーバーを再起動
```

#### 原因2: 埋め込みが生成されていない

**確認方法**:
- DynamoDBで単語に`embedding`フィールドがあるか確認
- 埋め込み生成スクリプトを実行したか

**解決方法**:
```bash
# 埋め込みを生成
python scripts/generate_embeddings.py --entity-type word --limit 10

# FAISSインデックスを構築
python scripts/build_faiss_index.py
```

#### 原因3: ツール関数が呼ばれていない

**確認方法**:
- サーバーログに `Tool calls made:` が表示されているか
- `No tool calls made for message:` が表示されているか

**解決方法**:
- Gemini APIがツール関数を呼ぶように、質問の形式を変える
- 例: "What does XXX mean?" → "Search for the word XXX"

#### 原因4: 結果の抽出に問題がある

**確認方法**:
- サーバーログの `Tool results:` を確認
- `word` フィールドに `id` が含まれているか

**解決方法**:
- `chat.py`の`word_ids`抽出ロジックを確認

## テストコマンド

### ログを確認しながらテスト

```bash
# 別ターミナルでサーバーを起動（ログを確認）
cd /Users/mo/Projects/japanese-learn-api/app/api/v1/chat
export PYTHONPATH="/Users/mo/Projects/japanese-learn-api/app/api/v1:$PYTHONPATH"
export S3_BUCKET_NAME="your-bucket-name"  # 必要に応じて
export AWS_REGION="ap-northeast-1"
export DYNAMODB_TABLE_NAME="japanese-learn-table"
uvicorn app:app --reload --port 8000

# 別ターミナルでテスト
./debug_chat.sh
```

### 個別テスト

```bash
# テスト1: 完全一致（日本語）
curl -X POST "http://127.0.0.1:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "What does こんにちは mean?", "session_id": "test-1"}'

# テスト2: ローマ字（意味検索が必要）
curl -X POST "http://127.0.0.1:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "What does konnichiwa mean?", "session_id": "test-2"}'
```

## 次のステップ

1. **サーバーログを確認** - エラーメッセージを特定
2. **環境変数を設定** - 必要に応じて設定
3. **埋め込みを生成** - まだ生成していない場合
4. **ログを共有** - 問題が解決しない場合、ログを共有してください

