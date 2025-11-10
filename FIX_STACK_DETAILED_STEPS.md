# スタック修正の詳細手順

## 現在の状況

- **スタック状態**: `UPDATE_FAILED`
- **失敗したリソース**: `CloudTrail`（IAM権限不足で作成失敗）
- **作成済みリソース**: `CloudTrailLogsBucket`、`CloudTrailLogsBucketPolicy`（S3バケットは手動削除済み）

## ⚠️ 重要な注意点

`UPDATE_FAILED`状態のスタックでは、通常の「ロールバックの続行」は利用できません。以下の方法で解決する必要があります。

## 解決方法

### 方法1: スタックを削除して再作成（データ保護が必要）

**⚠️ 警告**: この方法では、DynamoDBテーブルのデータを保護する設定が必要です。

#### ステップ1: DynamoDBテーブルにDeletionPolicyを追加

現在の`template.yaml`のDynamoDBテーブルに`DeletionPolicy: Retain`を追加します：

```yaml
  DynamoDBTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain  # ← これを追加
    Properties:
      TableName: !Sub ${AWS::StackName}-table
      # ... 既存の設定 ...
```

**この設定の意味**: スタックを削除しても、DynamoDBテーブルは削除されずに保持されます。

#### ステップ2: スタックを削除

AWSコンソールで：
1. CloudFormationコンソールを開く
2. `japanese-learn`スタックを選択
3. 「スタックの操作」→「スタックの削除」を選択
4. 確認して削除

**または、AWS CLIで**:

```bash
aws cloudformation delete-stack \
  --stack-name japanese-learn \
  --region ap-northeast-1
```

#### ステップ3: 削除の完了を待つ

```bash
# スタックの削除を監視
aws cloudformation wait stack-delete-complete \
  --stack-name japanese-learn \
  --region ap-northeast-1
```

#### ステップ4: スタックを再作成

```bash
make deploy
```

**この際、既存のDynamoDBテーブル名と同じ名前で作成されるため、既存のテーブルが使用されます。**

---

### 方法2: 手動でリソースを削除してからスタックを更新（推奨）

この方法は、スタックを削除せずに問題を解決できます。

#### ステップ1: CloudTrailLogsBucketPolicyを手動削除

S3バケットは既に削除済みなので、バケットポリシーも削除済みのはずですが、確認：

```bash
# バケットが存在しないことを確認
aws s3 ls | grep cloudtrail
```

#### ステップ2: スタックの状態を確認

```bash
aws cloudformation describe-stacks \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

#### ステップ3: スタックを更新（CloudTrailリソースを削除）

現在の`template.yaml`にはCloudTrailリソースが含まれていないため、デプロイを実行すると削除が試みられますが、`UPDATE_FAILED`状態では更新できません。

#### ステップ4: 一時的にCloudTrailリソースを追加して削除

`template.yaml`に一時的にCloudTrailリソースを追加し、`DeletionPolicy: Delete`を設定：

```yaml
  # 一時的な修正用（削除するため）
  CloudTrail:
    Type: AWS::CloudTrail::Trail
    DeletionPolicy: Delete  # 削除を許可
    Properties:
      TrailName: !Sub "${AWS::StackName}-trail"
      # 最小限の設定（作成を試みない）
      IsLogging: false  # ログを無効化

  CloudTrailLogsBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Delete
    Properties:
      BucketName: !Sub "${AWS::StackName}-cloudtrail-logs-temp"

  CloudTrailLogsBucketPolicy:
    Type: AWS::S3::BucketPolicy
    DeletionPolicy: Delete
    Properties:
      Bucket: !Ref CloudTrailLogsBucket
```

ただし、この方法は複雑です。

---

### 方法3: AWSサポートに連絡（最も安全）

AWSサポートに連絡して、失敗したリソースを手動で削除してもらう方法です。

---

## ✅ 推奨解決方法（最も簡単）

実際には、以下の方法が最も簡単です：

### ステップ1: DynamoDBテーブルにDeletionPolicyを追加

`template.yaml`を編集：

```yaml
  DynamoDBTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain  # スタック削除時もテーブルを保持
    Properties:
      # ... 既存の設定 ...
```

### ステップ2: スタックを削除

AWSコンソールで：
1. CloudFormation → `japanese-learn`スタック
2. 「スタックの操作」→「スタックの削除」
3. 確認して削除

### ステップ3: スタックを再作成

```bash
make deploy
```

**重要**: `DeletionPolicy: Retain`により、DynamoDBテーブルは保持され、再作成時に既存のテーブルが使用されます。

---

## 各方法の比較

| 方法 | 難易度 | 時間 | データ損失リスク | 推奨度 |
|------|--------|------|------------------|--------|
| **方法1（DeletionPolicy追加後削除）** | 🟡 中 | 10-30分 | ✅ なし（Retain設定時） | ⭐⭐⭐⭐⭐ |
| 方法2（手動削除） | 🔴 難 | 30-60分 | ✅ なし | ⭐⭐ |
| 方法3（AWSサポート） | 🟢 簡単 | 数時間 | ✅ なし | ⭐⭐⭐ |

---

## 次のステップ

どの方法を選択しますか？推奨は「方法1（DeletionPolicy追加後削除）」です。


