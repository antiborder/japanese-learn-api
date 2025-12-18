# CORSエラー デバッグチェックリスト

## 1. ブラウザの開発者ツールで確認する情報

### 1-1. エラーメッセージ（完全なテキスト）
ブラウザのコンソールに表示されるエラーメッセージを**完全に**コピーしてください。

### 1-2. Networkタブの情報
1. 開発者ツールのNetworkタブを開く
2. ページをリロードして、`/api/v1/chat/message`へのリクエストを探す
3. **OPTIONSリクエスト**（preflight）をクリックして、以下を確認：
   - **Request Headers**（特に`Origin`, `Access-Control-Request-Method`, `Access-Control-Request-Headers`）
   - **Response Headers**（特に`Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`）
   - **Status Code**（200か？それとも405/404/500か？）
   - **Response Body**（空か？エラーメッセージがあるか？）

4. **POSTリクエスト**（実際のリクエスト）をクリックして、以下を確認：
   - **Request Headers**
   - **Response Headers**
   - **Status Code**
   - **Response Body**

### 1-3. スクリーンショット
可能であれば、NetworkタブのOPTIONSリクエストとPOSTリクエストの詳細をスクリーンショットで共有してください。

## 2. Lambda関数のログを確認

以下のコマンドを実行して、Lambda関数のログを確認してください：

```bash
# 最新のログを確認（OPTIONSリクエスト関連）
aws logs tail $(aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/japanese-learn-Chat" --query 'logGroups[0].logGroupName' --output text) --since 1h --format short | grep -E "(OPTIONS|CORS|cors|preflight|httpMethod|405|200)" | tail -30
```

## 3. curlで直接テスト

以下のコマンドを実行して、OPTIONSリクエストのレスポンスを確認してください：

```bash
# OPTIONSリクエスト（preflight）のテスト
curl -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v \
  https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/chat/message 2>&1

# 実際のPOSTリクエストのテスト
curl -X POST \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}' \
  -v \
  https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/chat/message 2>&1
```

## 4. API Gatewayの設定確認

以下のコマンドでAPI Gatewayのメソッド設定を確認してください：

```bash
# API GatewayのリソースIDを取得
API_ID=$(aws cloudformation describe-stacks --stack-name japanese-learn --query 'Stacks[0].Outputs[?OutputKey==`ApiId`].OutputValue' --output text)

# /api/v1/chatリソースのメソッドを確認
aws apigateway get-resource --rest-api-id $API_ID --resource-id $(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?path==`/api/v1/chat`].id' --output text) --query 'resourceMethods' --output json

# /api/v1/chat/{proxy+}リソースのメソッドを確認
aws apigateway get-resources --rest-api-id $API_ID --query 'items[?path==`/api/v1/chat/{proxy+}`]' --output json
```

## 5. フロントエンドのリクエストコード

フロントエンドから送信されているリクエストのコード（特に`fetch`や`axios`の設定）を確認してください。
特に以下を確認：
- リクエストヘッダー（`Content-Type`など）
- リクエストメソッド（`POST`など）
- リクエストURL

## 6. 現在のLambda関数コード

`app/api/v1/chat/app.py`の現在の内容を確認してください。

