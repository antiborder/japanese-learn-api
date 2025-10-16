# AI解説機能セットアップガイド

このガイドでは、Gemini APIを使用したAI単語解説機能のセットアップ方法を説明します。

## 概要

この機能は、日本語の単語についてAI（Gemini 2.5 Flash-Lite）がユーザーの母国語で解説を提供します。
生成された解説はS3に永続化され、2回目以降のリクエストではキャッシュから取得されます。

## 必要な設定

### 1. Gemini APIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. "Create API Key" をクリック
4. 新しいプロジェクトを選択または作成
5. APIキーをコピー

### 2. 環境変数の設定

`.env` ファイルまたは環境変数に以下を追加：

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# AWS S3 (既存の設定)
S3_BUCKET_NAME=japanese-learn-api-resource
AWS_REGION=ap-northeast-1
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

新しく追加された依存関係：
- `google-generativeai` - Gemini API クライアント

## API仕様

### エンドポイント

```
GET /words/{word_id}/ai-description
```

### クエリパラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|------|------|-----------|------|
| lang | string | いいえ | en | 言語コード |

### 対応言語

| 言語コード | 言語名 |
|-----------|-------|
| en | English (英語) |
| vi | Vietnamese (ベトナム語) |
| zh | Chinese (中国語) |
| hi | Hindi (ヒンディー語) |
| es | Spanish (スペイン語) |
| fr | French (フランス語) |
| de | German (ドイツ語) |
| pt | Portuguese (ポルトガル語) |
| ru | Russian (ロシア語) |
| ja | Japanese (日本語) |
| ko | Korean (韓国語) |
| ar | Arabic (アラビア語) |
| th | Thai (タイ語) |
| id | Indonesian (インドネシア語) |

### リクエスト例

```bash
# 英語で解説を取得
curl "http://localhost:8000/api/v1/words/100/ai-description?lang=en"

# ベトナム語で解説を取得
curl "http://localhost:8000/api/v1/words/100/ai-description?lang=vi"

# 中国語で解説を取得
curl "http://localhost:8000/api/v1/words/100/ai-description?lang=zh"
```

### レスポンス例

```json
{
  "word_id": 100,
  "word_name": "こんにちは",
  "language": "en",
  "description": "【意味】\n\"こんにちは\" (konnichiwa) is a common Japanese greeting...\n\n【具体例】\n...\n\n【類義語】\n...\n\n【対義語】\n...\n\n【使い方】\n...\n\n【例文1】\n...\n\n【例文2】\n...\n\n【語源】\n..."
}
```

### エラーレスポンス

#### 404 Not Found
```json
{
  "detail": "Word name not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Failed to fetch AI description: <エラーメッセージ>"
}
```

## S3構造

生成されたAI解説は以下のパスに保存されます：

```
s3://{bucket_name}/ai_descriptions/words/{word_id}_{lang_code}.txt
```

例：
- `ai_descriptions/words/100_en.txt` - 単語ID 100の英語解説
- `ai_descriptions/words/100_vi.txt` - 単語ID 100のベトナム語解説
- `ai_descriptions/words/200_zh.txt` - 単語ID 200の中国語解説

## 処理フロー

1. クライアントがエンドポイントをリクエスト
2. DynamoDBから単語情報を取得
3. S3にキャッシュされた解説が存在するかチェック
   - **存在する場合**: S3から取得して返却
   - **存在しない場合**: 
     1. Gemini APIで解説を生成
     2. S3に保存（キャッシュ）
     3. 生成された解説を返却

## コスト最適化

- **キャッシュ機能**: 一度生成された解説はS3に保存され、2回目以降のリクエストではAI生成が行われません
- **効率的なモデル**: Gemini 2.5 Flash-Liteは高速かつ低コストなモデルです

## トラブルシューティング

### APIキーエラー

```
GEMINI_API_KEY is not configured
```

**解決方法**: 環境変数 `GEMINI_API_KEY` が正しく設定されているか確認してください。

### モデルエラー

```
Model not found: gemini-2.0-flash-lite
```

**解決方法**: 
- Gemini 2.5 Flash-Liteの正式なモデル名を確認
- `gemini_integration.py` の `model` 変数を更新
- 利用可能なモデル一覧: [Google AI Models](https://ai.google.dev/models)

### S3保存エラー

S3への保存に失敗しても、生成された解説は返却されます（ログに警告が記録されます）。
次回のリクエスト時に再生成されます。

## 開発者向け情報

### ファイル構成

```
app/api/v1/words/
├── endpoints/
│   └── word.py                           # エンドポイント定義
├── integrations/
│   ├── aws_integration.py                # S3操作（新機能追加）
│   └── gemini_integration.py             # Gemini API連携（新規作成）
└── services/
    └── ai_description_service.py         # ビジネスロジック（新規作成）
```

### カスタマイズ

#### プロンプトの変更

`gemini_integration.py` の `create_description_prompt()` 関数を編集することで、
AI解説の構造や内容をカスタマイズできます。

#### 言語の追加

`gemini_integration.py` の `LANGUAGE_NAMES` 辞書に新しい言語を追加してください：

```python
LANGUAGE_NAMES = {
    'en': 'English',
    'vi': 'Vietnamese',
    'your_code': 'Your Language Name',
    # ...
}
```

#### モデルの変更

より高性能なモデルが必要な場合は、`gemini_integration.py` のモデル名を変更：

```python
# 例: より高性能なモデルを使用
model = genai.GenerativeModel('gemini-1.5-pro')
```

## テスト

### ローカルテスト

```bash
# サーバーを起動
uvicorn app.main:app --reload

# テストリクエスト
curl "http://localhost:8000/api/v1/words/1/ai-description?lang=en"
```

### デプロイ後のテスト

```bash
# デプロイされたエンドポイントをテスト
curl "https://your-api-domain.com/api/v1/words/1/ai-description?lang=vi"
```

## 参考リンク

- [Google AI Studio](https://makersuite.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

## ライセンス

このプロジェクトのライセンスに従います。


