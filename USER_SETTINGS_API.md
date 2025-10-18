# ユーザー設定API

ユーザーがベースレベル、テーマ、言語を設定できるAPI機能を実装しました。

## 機能概要

- **ベースレベル**: 1〜15の範囲で設定可能
- **テーマ**: SummerまたはFallを選択可能
- **言語**: en（英語）またはvi（ベトナム語）を選択可能

## API エンドポイント

### 1. ユーザー設定の取得
```
GET /api/v1/users/settings
```

**認証**: Bearerトークン必須

**レスポンス例**:
```json
{
  "user_id": "user-123",
  "base_level": 5,
  "theme": "Summer",
  "language": "en",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 2. ユーザー設定の作成
```
POST /api/v1/users/settings
```

**認証**: Bearerトークン必須

**リクエストボディ**:
```json
{
  "base_level": 5,
  "theme": "Summer",
  "language": "en"
}
```

**レスポンス**: 作成された設定情報

### 3. ユーザー設定の更新
```
PUT /api/v1/users/settings
```

**認証**: Bearerトークン必須

**リクエストボディ** (部分更新対応):
```json
{
  "base_level": 8,
  "theme": "Fall"
}
```

**レスポンス**: 更新された設定情報

### 4. ユーザー設定の削除
```
DELETE /api/v1/users/settings
```

**認証**: Bearerトークン必須

**レスポンス**:
```json
{
  "message": "User settings deleted successfully"
}
```

## テスト用エンドポイント

開発・テスト用に認証をバイパスするエンドポイントも提供しています：

- `GET /api/v1/users/test/settings`
- `POST /api/v1/users/test/settings`

## データベース構造

DynamoDBのアイテム構造：
```
PK: USER#{user_id}
SK: SETTINGS
base_level: 数値 (1-15)
theme: 文字列 ("Summer" または "Fall")
language: 文字列 ("en" または "vi")
created_at: ISO8601形式の日時
updated_at: ISO8601形式の日時
```

## マイグレーション

既存のユーザーにデフォルト設定を追加する場合：

```bash
python scripts/migrate_user_settings.py
```

デフォルト設定：
- base_level: 1
- theme: "Summer"
- language: "en"

## エラーハンドリング

- **404**: ユーザー設定が見つからない場合
- **409**: 既存の設定がある状態でPOSTを実行した場合
- **422**: バリデーションエラー（無効な値など）
- **500**: サーバー内部エラー

## 使用例

### 設定の作成
```bash
curl -X POST "https://your-api.com/api/v1/users/settings" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "base_level": 5,
    "theme": "Summer",
    "language": "en"
  }'
```

### 設定の更新
```bash
curl -X PUT "https://your-api.com/api/v1/users/settings" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "base_level": 8,
    "theme": "Fall"
  }'
```

### 設定の取得
```bash
curl -X GET "https://your-api.com/api/v1/users/settings" \
  -H "Authorization: Bearer your-token"
```
