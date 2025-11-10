# AWSコンソールでのスタック修正手順

## 現在の状況

- **スタック名**: `japanese-learn`
- **状態**: `UPDATE_FAILED`
- **原因**: CloudTrailリソースの作成失敗（IAM権限不足）

## AWSコンソールでの操作手順

### ⚠️ UPDATE_FAILED状態で利用可能なオプション

`UPDATE_FAILED`状態のスタックでは、以下のオプションが利用可能です：

1. **スタックの削除 (Delete stack)**
2. **スタックの詳細の表示 (View stack details)**
3. **変更セットの表示 (View change sets)**

**重要**: `UPDATE_FAILED`状態では、「ロールバックの続行」は通常利用できません。

---

## ✅ 推奨解決方法：データを保護してスタックを再作成

### ステップ1: DynamoDBテーブルにDeletionPolicyを追加

**目的**: スタックを削除しても、DynamoDBテーブルのデータを保持するため

`template.yaml`のDynamoDBテーブル定義に以下を追加：

```yaml
  DynamoDBTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain  # ← これを追加（スタック削除時もテーブルを保持）
    Properties:
      TableName: !Sub ${AWS::StackName}-table
      # ... 既存の設定 ...
```

**この設定により**: スタックを削除しても、DynamoDBテーブル `japanese-learn-table` は削除されずに残ります。

### ステップ2: AWSコンソールでスタックを削除

**操作手順**:

1. **CloudFormationコンソールを開く**
   - AWSマネジメントコンソール → 「CloudFormation」を検索

2. **スタックを選択**
   - スタック一覧から `japanese-learn` をクリック

3. **スタックの操作メニューを開く**
   - 右上の「スタックの操作」ボタンをクリック
   - ドロップダウンメニューが表示されます

4. **「スタックの削除」を選択**
   - メニューから「スタックの削除 (Delete stack)」を選択
   - 確認ダイアログが表示されます

5. **削除を確認**
   - 「スタックの削除」ボタンをクリック
   - スタックの削除が開始されます

**削除にかかる時間**: 通常5-15分

### ステップ3: 削除の完了を待つ

**確認方法**:

1. CloudFormationコンソールでスタック一覧を確認
2. `japanese-learn`スタックが表示されなくなるまで待つ
3. または、「イベント」タブで削除の進行状況を確認

**削除が完了したら**: スタック一覧から `japanese-learn` が消えます

### ステップ4: スタックを再作成

**目的**: 正常な状態でスタックを再作成

```bash
make deploy
```

**重要**: `DeletionPolicy: Retain`により、既存のDynamoDBテーブル `japanese-learn-table` が使用されます。データは保持されます。

---

## 削除後の確認事項

### DynamoDBテーブルの確認

スタックを削除した後、DynamoDBテーブルが保持されていることを確認：

```bash
# DynamoDBテーブルが存在することを確認
aws dynamodb describe-table \
  --table-name japanese-learn-table \
  --region ap-northeast-1
```

**期待される結果**: テーブルが存在し、データが保持されている

### スタック再作成後の確認

デプロイ後、以下を確認：

```bash
# スタックの状態を確認
aws cloudformation describe-stacks \
  --stack-name japanese-learn \
  --region ap-northeast-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

**期待される結果**: `CREATE_COMPLETE`

---

## 注意事項

### ✅ 安全な点

- **DynamoDBデータ**: `DeletionPolicy: Retain`により、データは保持されます
- **既存のテーブル使用**: スタック再作成時、既存のテーブル名を使用するため、既存のテーブルがそのまま使用されます

### ⚠️ 注意が必要な点

1. **サービス停止時間**: スタック削除中は、Lambda関数やAPI Gatewayが利用できません（5-15分）
2. **Cognito User Pool**: ユーザー情報は削除されます（再作成が必要）
3. **API Gateway URL**: 新しいURLが生成される可能性があります

### 🔍 削除されるリソース

- Lambda関数（すべて）
- API Gateway
- Cognito User Pool
- CloudWatch Log Groups
- IAMロール
- **DynamoDBテーブルは保持される**（`DeletionPolicy: Retain`設定時）

---

## まとめ

### AWSコンソールで選択するオプション

**「スタックの操作」→「スタックの削除 (Delete stack)」**

### 実行手順

1. ✅ `template.yaml`に`DeletionPolicy: Retain`を追加
2. ✅ AWSコンソールでスタックを削除
3. ✅ 削除完了を待つ（5-15分）
4. ✅ `make deploy`でスタックを再作成

### データ保護

- ✅ DynamoDBテーブルは保持されます
- ✅ データは失われません
- ⚠️ Cognitoユーザー情報は削除されます（再登録が必要）


