# デプロイエラーの解決方法

## エラーの原因

```
Recreating a resource that is pending clean up is not allowed for disable rollback. 
Please try with different logical IDs for resources [ServerlessRestApiDeploymentc84be87a31]
```

このエラーは、API Gateway Deploymentリソースが削除中の状態で、同じ論理IDで再作成しようとしているために発生しています。

## ⚠️ スタック削除の影響

**スタックを削除すると、以下のリソースが削除されます**：

### 削除されるリソース

1. **DynamoDBテーブル** (`japanese-learn-table`)
   - ⚠️ **データがすべて削除されます**
   - 再作成が必要です
   - データの復元が必要です（バックアップから）

2. **Lambda関数**（すべて）
   - WordsFunction
   - LearnWordsFunction
   - UsersFunction
   - KanjisFunction
   - SearchFunction
   - SentencesFunction
   - SentenceCompositionFunction
   - 再デプロイが必要です

3. **API Gateway**
   - すべてのエンドポイントが削除されます
   - URLが変わります

4. **Cognito User Pool**
   - ユーザー情報が削除されます
   - 再作成が必要です

5. **CloudWatch Log Groups**
   - ログが削除されます

6. **IAMロール**
   - 再作成が必要です

## ✅ 安全な解決方法（推奨）

### 方法1: スタックの状態を確認して待つ（最も安全）

削除中のリソースが完了するまで待ちます：

```bash
# スタックの状態を確認
aws cloudformation describe-stacks \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'Stacks[0].StackStatus' \
  --output text

# 削除中のリソースを確認
aws cloudformation list-stack-resources \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'StackResourceSummaries[?ResourceStatus==`DELETE_IN_PROGRESS`]'
```

**削除が完了したら**（通常数分）、再度デプロイを実行：

```bash
make deploy
```

### 方法2: 問題のあるリソースだけを修正

API Gateway Deploymentリソースの論理IDを変更することで解決できます：

#### オプションA: SAMの自動生成を無効化（推奨）

`template.yaml`に以下を追加：

```yaml
Globals:
  Api:
    # API Gateway Deploymentの自動生成を無効化
    DeploymentPreference:
      Type: AllAtOnce
    # 既存の設定...
    Cors:
      AllowMethods: "'GET,POST,PUT,DELETE,OPTIONS'"
      AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Origin,Accept'"
      AllowOrigin: "'*'"
```

ただし、これはSAMのServerlessRestApiの自動生成に影響する可能性があります。

#### オプションB: 一時的に`disable_rollback`を無効化

`samconfig.toml`を編集：

```toml
[default.deploy.parameters]
stack_name = "japanese-learn"
region = "ap-northeast-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
disable_rollback = false  # falseに変更
```

その後、デプロイを再実行：

```bash
make deploy
```

#### オプションC: 手動でAPI Gateway Deploymentを削除

1. AWSコンソールでAPI Gatewayを開く
2. 削除中のDeploymentを見つける
3. 削除が完了するまで待つ
4. 再度デプロイ

### 方法3: 変更セットをキャンセルして再試行

```bash
# 最新の変更セットを確認
aws cloudformation list-change-sets \
  --stack-name japanese-learn \
  --region ap-northeast-1

# 失敗した変更セットを削除
aws cloudformation delete-change-set \
  --change-set-name <変更セット名> \
  --stack-name japanese-learn \
  --region ap-northeast-1

# 再度デプロイ
make deploy
```

## 🔍 現在のスタック状態を確認

```bash
# スタックの状態を確認
aws cloudformation describe-stacks \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'Stacks[0].[StackStatus,StackStatusReason]' \
  --output table

# 削除中のリソースを確認
aws cloudformation list-stack-resources \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'StackResourceSummaries[?contains(ResourceStatus, `DELETE`)]' \
  --output table

# イベントを確認
aws cloudformation describe-stack-events \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --max-items 20 \
  --query 'StackEvents[*].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId,ResourceStatusReason]' \
  --output table
```

## 💡 推奨される手順

1. **まず、スタックの状態を確認**
   ```bash
   aws cloudformation describe-stacks --stack-name japanese-learn --region ap-northeast-1
   ```

2. **削除中のリソースがある場合、完了するまで待つ**（通常5-10分）

3. **待っている間に、`samconfig.toml`で`disable_rollback = false`に変更**

4. **削除が完了したら、再度デプロイ**
   ```bash
   make deploy
   ```

## ⚠️ 注意事項

- **データのバックアップ**: DynamoDBテーブルに重要なデータがある場合、事前にバックアップを取ることを推奨します
- **サービス停止**: スタックを削除すると、サービスが停止します
- **URL変更**: API GatewayのURLが変わる可能性があります

## 参考

このエラーは、CloudTrailやIAMポリシーの変更とは**全く関係ありません**。API Gateway Deploymentリソースの管理に関する問題です。


