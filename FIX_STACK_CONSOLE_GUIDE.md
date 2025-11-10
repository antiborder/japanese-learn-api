# AWSコンソールでスタックを修正する手順

## 現在の状況

- スタック名: `japanese-learn`
- 状態: `UPDATE_FAILED`
- 原因: CloudTrailリソースの作成失敗（IAM権限不足）

## AWSコンソールでの操作手順

### 方法1: ロールバックを続行する（推奨）

`UPDATE_FAILED`状態のスタックでは、以下の手順でロールバックを続行できます：

#### ステップ1: CloudFormationコンソールを開く

1. AWSマネジメントコンソールにログイン
2. 「CloudFormation」サービスを検索して開く
3. スタック一覧から `japanese-learn` を選択

#### ステップ2: スタック操作メニューを開く

1. スタックの詳細ページで、右上の「スタックの操作」ボタンをクリック
2. ドロップダウンメニューが表示されます

#### ステップ3: 「ロールバックの続行」を選択

**⚠️ 重要**: `UPDATE_FAILED`状態では、以下のオプションが利用可能です：

- **「ロールバックの続行 (Continue update rollback)」** ← これを選択

#### ステップ4: 失敗したリソースをスキップ

1. 「ロールバックの続行」をクリック
2. モーダルウィンドウが開きます
3. 「スキップするリソース」セクションで：
   - `CloudTrail` を入力（失敗したリソース）
   - `CloudTrailLogsBucket` を入力（作成済みだが削除したい）
   - `CloudTrailLogsBucketPolicy` を入力（作成済みだが削除したい）
4. 「ロールバックの続行」ボタンをクリック

**これにより**:
- 失敗したCloudTrailリソースがスキップされます
- 作成済みのS3バケットとバケットポリシーが削除されます
- スタックが正常な状態（`UPDATE_ROLLBACK_COMPLETE`）に戻ります

#### ステップ5: デプロイを再実行

ロールバックが完了したら（通常5-10分）、再度デプロイを実行：

```bash
make deploy
```

---

### 方法2: スタックからのリソースの削除（UPDATE_FAILED状態では利用不可）

**注意**: `UPDATE_FAILED`状態のスタックでは、「スタックからのリソースの削除」オプションは通常利用できません。

このオプションは、正常な状態（`UPDATE_COMPLETE`など）のスタックでのみ利用可能です。

---

## AWS CLIでロールバックを続行する方法

コンソールの操作が難しい場合は、AWS CLIでも実行できます：

### ステップ1: 失敗したリソースをスキップしてロールバックを続行

```bash
# 失敗したCloudTrailリソースをスキップしてロールバックを続行
aws cloudformation continue-update-rollback \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --resources-to-skip CloudTrail CloudTrailLogsBucket CloudTrailLogsBucketPolicy
```

**このコマンドの意味**:
- `continue-update-rollback`: ロールバックを続行する
- `--resources-to-skip`: これらのリソースをスキップ（削除を試みない）

### ステップ2: ロールバックの完了を待つ

```bash
# スタックの状態を監視
aws cloudformation wait stack-rollback-complete \
  --stack-name japanese-learn \
  --region ap-northeast-1
```

または、状態を確認：

```bash
# スタックの状態を確認
aws cloudformation describe-stacks \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

`UPDATE_ROLLBACK_COMPLETE` になれば完了です。

### ステップ3: 再度デプロイ

```bash
make deploy
```

---

## 手順の比較

| 方法 | 難易度 | 時間 | リスク |
|------|--------|------|--------|
| **AWSコンソール（ロールバックの続行）** | 🟢 簡単 | 5-10分 | なし |
| **AWS CLI（ロールバックの続行）** | 🟡 中 | 5-10分 | なし |
| スタックの削除 | 🔴 難 | 10-30分 | ⚠️ データ損失の可能性 |

---

## 推奨手順（最も簡単）

### オプションA: AWSコンソールを使用（推奨）

1. CloudFormationコンソールを開く
2. `japanese-learn`スタックを選択
3. 「スタックの操作」→「ロールバックの続行」を選択
4. スキップするリソースに以下を入力：
   - `CloudTrail`
   - `CloudTrailLogsBucket`
   - `CloudTrailLogsBucketPolicy`
5. 「ロールバックの続行」をクリック
6. 完了を待つ（5-10分）
7. `make deploy` を実行

### オプションB: AWS CLIを使用

以下のコマンドを実行：

```bash
# ロールバックを続行
aws cloudformation continue-update-rollback \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --resources-to-skip CloudTrail CloudTrailLogsBucket CloudTrailLogsBucketPolicy

# 完了を待つ（オプション）
aws cloudformation wait stack-rollback-complete \
  --stack-name japanese-learn \
  --region ap-northeast-1

# 状態を確認
aws cloudformation describe-stacks \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

完了後、`make deploy` を実行してください。

---

## 注意事項

- **データ損失なし**: この操作でDynamoDBテーブルやその他の重要なリソースは影響を受けません
- **サービス停止なし**: 既存のLambda関数やAPI Gatewayは正常に動作し続けます
- **ロールバック時間**: 通常5-10分かかります

---

## トラブルシューティング

### エラー: "ContinueUpdateRollback cannot be called from stack with UPDATE_FAILED status"

このエラーが出る場合は、スタックの状態を確認：

```bash
aws cloudformation describe-stacks \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

`UPDATE_FAILED`状態の場合、まず失敗した変更セットを削除する必要がある場合があります。


