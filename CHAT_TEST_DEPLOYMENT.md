# ChatTestFunction Lambda Container デプロイ手順

## 概要
ChatTestFunctionはLambdaコンテナイメージとしてデプロイされます。250MBの容量制限を超える可能性があるため、コンテナイメージ方式を使用しています。

## 前提条件
- AWS CLIが設定されていること
- Dockerがインストールされていること
- ECRリポジトリを作成する権限があること（管理者権限が必要）

## デプロイ手順

### 1. ECRリポジトリの作成

ECRリポジトリを手動で作成します：

```bash
# スクリプトを使用する場合
./scripts/create_ecr_repository.sh

# または、手動で作成する場合
aws ecr create-repository \
  --repository-name japanese-learn-chattestfunction \
  --region ap-northeast-1 \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability MUTABLE
```

### 2. DockerイメージのビルドとECRへのプッシュ

```bash
./scripts/build_and_push_chat_test.sh
```

このスクリプトは以下を実行します：
1. ECRリポジトリの存在確認
2. Dockerイメージのビルド（x86_64アーキテクチャ）
3. ECRへのログイン
4. イメージのタグ付け
5. ECRへのプッシュ

### 3. Lambda関数のデプロイ

```bash
sam deploy --no-confirm-changeset --no-fail-on-empty-changeset --resolve-s3
```

## トラブルシューティング

### ECRリポジトリの作成権限エラー
ECRリポジトリの作成権限がない場合は、管理者に依頼してリポジトリを作成してもらうか、AWSコンソールから手動で作成してください。

### Dockerイメージのビルドエラー
Dockerが正しくインストールされているか確認してください：
```bash
docker --version
docker buildx version
```

### Lambda関数の更新
Dockerイメージを更新した後、Lambda関数を更新するには：
```bash
aws lambda update-function-code \
  --function-name japanese-learn-ChatTestFunction \
  --image-uri <ECR_URI>:latest \
  --region ap-northeast-1
```

## ファイル構成

- `app/api/v1/chat-test/app.py` - Lambdaハンドラー
- `app/api/v1/chat-test/Dockerfile` - Dockerイメージ定義
- `scripts/build_and_push_chat_test.sh` - ビルド・プッシュスクリプト
- `scripts/create_ecr_repository.sh` - ECRリポジトリ作成スクリプト

