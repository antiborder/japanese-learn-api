# Chat CORS エラーのデバッグガイド

## 問題の概要
`/api/v1/chat/message`へのOPTIONSリクエストが`403 Missing Authentication Token`を返しています。
これは、API GatewayがリクエストをLambda関数にルーティングできていないことを示します。

## デバッグ手順

### 1. API Gatewayのリソースとメソッドを確認

```bash
# API Gateway IDを取得
API_ID="omqihdsdi1"

# /api/v1/chatリソースのIDを取得
CHAT_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/api/v1/chat'].id" \
  --output text)

echo "Chat Resource ID: $CHAT_RESOURCE_ID"

# /api/v1/chat/{proxy+}リソースのIDを取得
CHAT_PROXY_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/api/v1/chat/{proxy+}'].id" \
  --output text)

echo "Chat Proxy Resource ID: $CHAT_PROXY_RESOURCE_ID"

# ChatApiResourceのANYメソッドを確認
aws apigateway get-method \
  --rest-api-id $API_ID \
  --resource-id $CHAT_RESOURCE_ID \
  --http-method ANY

# ChatApiProxyResourceのANYメソッドを確認
aws apigateway get-method \
  --rest-api-id $API_ID \
  --resource-id $CHAT_PROXY_RESOURCE_ID \
  --http-method ANY
```

### 2. Lambda関数のログを確認

```bash
# 最新のログを確認（OPTIONSリクエストがLambda関数に到達しているか）
aws logs tail /aws/lambda/japanese-learn-ChatFunction-PmJov4LcbytD \
  --since 10m \
  --format short \
  | grep -E "(OPTIONS|CORS|cors|origin|Origin|Received event)" \
  | tail -50
```

### 3. OPTIONSリクエストをテスト

```bash
# 許可されたOriginからのOPTIONSリクエスト
curl -X OPTIONS \
  -H "Origin: https://nihongo.cloud" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v \
  https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/chat/message

# 許可されていないOriginからのOPTIONSリクエスト
curl -X OPTIONS \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v \
  https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/chat/message
```

### 4. API Gatewayのデプロイメントを確認

```bash
# 最新のデプロイメントIDを確認
aws apigateway get-deployments \
  --rest-api-id $API_ID \
  --query "items[0].{Id:id,CreatedDate:createdDate,Description:description}" \
  --output table

# デプロイメントを作成（必要に応じて）
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name Prod \
  --description "Force deployment for CORS fix"
```

### 5. CloudFormationスタックの状態を確認

```bash
# スタックの状態を確認
aws cloudformation describe-stacks \
  --stack-name japanese-learn \
  --query "Stacks[0].StackStatus" \
  --output text

# 失敗したリソースを確認
aws cloudformation describe-stack-resources \
  --stack-name japanese-learn \
  --query "StackResources[?ResourceStatus=='UPDATE_FAILED' || ResourceStatus=='DELETE_FAILED']" \
  --output table
```

## 考えられる原因

1. **API Gatewayのメソッドが正しく設定されていない**
   - `ChatApiProxyMethod`の`Method: ANY`が正しくデプロイされていない可能性
   - スタックのロールバックにより、メソッドが削除された可能性

2. **API Gatewayのデプロイメントが古い**
   - 最新の変更がデプロイされていない可能性

3. **リソースIDの不一致**
   - `ChatApiResource`や`ChatApiProxyResource`のIDが正しく参照されていない可能性

## 解決策

### オプション1: スタックを再デプロイ
```bash
# スタックを再デプロイ（OPTIONSメソッドの削除を反映）
make deploy
```

### オプション2: API Gatewayを手動でデプロイ
```bash
# 最新のデプロイメントを作成
aws apigateway create-deployment \
  --rest-api-id omqihdsdi1 \
  --stage-name Prod \
  --description "Force deployment for CORS fix"
```

### オプション3: Lambda関数のコードを確認
- `app/api/v1/chat/app.py`でOPTIONSリクエストの処理が正しく実装されているか確認
- コンテナイメージが最新のコードを含んでいるか確認（再ビルドが必要な場合あり）

