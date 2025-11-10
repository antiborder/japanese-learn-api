# CloudTrail検索例：WordsFunctionのログを検索する方法

## 概要

このドキュメントでは、CloudTrailを使用してWordsFunctionのLambda関数のログを検索する具体的な方法を説明します。

## WordsFunctionについて

- **関数名**: `japanese-learn-WordsFunction`（スタック名が `japanese-learn` の場合）
- **主な機能**: 単語データの取得、音声ファイルの取得、画像の取得、AI解説の取得
- **使用するAWSサービス**:
  - **DynamoDB**: 単語データの読み取り（Query, GetItem）
  - **S3**: 音声ファイル、画像、AI解説の保存・取得（PutObject, GetObject, ListBucket）

## 検索方法

### 方法1: Lambda関数のリソース名で検索（最も簡単）

#### AWS CLI

```bash
# WordsFunctionに関連するすべてのイベントを検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-WordsFunction \
  --max-results 100
```

#### CloudTrailコンソール

1. CloudTrailコンソールを開く
2. 「イベント履歴」を選択
3. フィルタに以下を設定:
   - **リソース名**: `japanese-learn-WordsFunction`
4. 時間範囲を選択（例: 過去7日間）

**結果**: 
- Lambda関数の作成・更新・削除イベント
- Lambda関数の設定変更イベント
- その他のLambda関数に関連する管理イベント

---

### 方法2: WordsFunctionが実行したDynamoDB操作を検索

WordsFunctionは以下のDynamoDB操作を実行します：
- `Query`: 単語一覧の取得
- `GetItem`: 特定の単語の取得

#### AWS CLI

```bash
# このアプリのテーブルへのQuery操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=Query \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100

# このアプリのテーブルへのGetItem操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=GetItem \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100
```

#### CloudTrailコンソール

1. CloudTrailコンソールを開く
2. 「イベント履歴」を選択
3. フィルタに以下を設定:
   - **イベント名**: `Query` または `GetItem`
   - **リソース名**: `japanese-learn-table`
4. 時間範囲を選択

**注意**: この方法では、このアプリのテーブルへのすべてのQuery/GetItem操作が表示されます。WordsFunction以外のLambda関数（LearnWordsFunction、SearchFunctionなど）の操作も含まれます。

---

### 方法3: Lambda関数のIAMロール名で検索（最も正確）

WordsFunctionが使用するIAMロール名から検索することで、WordsFunctionが実行した操作のみを正確に特定できます。

#### ステップ1: WordsFunctionのロール名を確認

```bash
# Lambda関数の設定からロール名を確認
aws lambda get-function-configuration \
  --function-name japanese-learn-WordsFunction \
  --query 'Role' \
  --output text

# 例: arn:aws:iam::123456789012:role/japanese-learn-WordsFunctionRole-ABC123XYZ
```

#### ステップ2: ロール名でCloudTrailを検索

```bash
# ロール名から実行された操作を検索
# 注意: 実際のアカウントIDとロール名に置き換えてください
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=arn:aws:sts::123456789012:assumed-role/japanese-learn-WordsFunctionRole-ABC123XYZ/* \
  --max-results 100
```

**結果**: WordsFunctionのロールから実行されたすべての操作が表示されます。

---

### 方法4: 過去24時間のWordsFunctionの操作を確認

#### AWS CLI

```bash
# 過去24時間のこのアプリのテーブルへの操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 1000
```

結果をJSONで処理して、WordsFunctionに関連する操作を抽出：

```bash
# jqを使用してフィルタリング
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 1000 \
  | jq '.Events[] | select(.CloudTrailEvent | contains("WordsFunction") or contains("Query") or contains("GetItem"))'
```

---

### 方法5: 特定のイベント名で検索

#### WordsFunctionが実行する可能性があるイベント

- **DynamoDB操作**:
  - `Query`: 単語一覧の取得
  - `GetItem`: 特定の単語の取得

- **S3操作**:
  - `PutObject`: 音声ファイルや画像の保存
  - `GetObject`: 音声ファイルや画像の取得
  - `ListBucket`: バケットの一覧取得

- **Lambda関数の管理操作**:
  - `CreateFunction`: 関数の作成
  - `UpdateFunctionCode`: コードの更新
  - `UpdateFunctionConfiguration`: 設定の更新

#### 検索例

```bash
# Query操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=Query \
  --max-results 100

# GetItem操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetItem \
  --max-results 100

# S3 PutObject操作を検索（WordsFunctionが音声ファイルを保存する場合）
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutObject \
  --max-results 100
```

---

## 実用的な検索コマンド集

### 1. WordsFunctionに関連するすべてのイベント（過去7日間）

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-WordsFunction \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 500
```

### 2. WordsFunctionが実行したDynamoDB操作（過去24時間）

```bash
# Query操作
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=Query \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 1000

# GetItem操作
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=GetItem \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 1000
```

### 3. WordsFunctionのエラーを確認

```bash
# DynamoDBエラーを検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100 \
  | jq '.Events[] | select(.CloudTrailEvent | contains("error") or contains("Error") or contains("exception") or contains("Exception"))'

# または、レスポンスコードでフィルタ
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100 \
  | jq '.Events[] | select(.ResponseElements.errorCode != null)'
```

### 4. WordsFunctionの使用頻度を確認

```bash
# 過去24時間のQuery操作の回数をカウント
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=Query \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 10000 \
  | jq '.Events | length'

# 時間帯ごとの操作数を確認
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=Query \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 10000 \
  | jq '.Events[] | .EventTime' | cut -d'T' -f2 | cut -d':' -f1 | sort | uniq -c
```

---

## CloudTrailコンソールでの検索方法

### ステップ1: CloudTrailコンソールを開く

1. AWSマネジメントコンソールにログイン
2. 「CloudTrail」サービスを検索して開く
3. 左側のメニューから「イベント履歴（Event history）」を選択

### ステップ2: フィルタリング設定

#### オプション1: Lambda関数名でフィルタ

- **リソース名**: `japanese-learn-WordsFunction`
- **時間範囲**: 過去7日間

#### オプション2: DynamoDBテーブル名とイベント名でフィルタ

- **イベント名**: `Query` または `GetItem`
- **リソース名**: `japanese-learn-table`
- **時間範囲**: 過去24時間

### ステップ3: 結果の確認

各イベントをクリックすると、以下の情報が表示されます：
- **イベント時間**: イベントが発生した日時
- **ユーザー名**: WordsFunctionのIAMロール名
- **イベント名**: 実行されたAPI操作（Query、GetItemなど）
- **リソース名**: 操作対象のリソース（DynamoDBテーブル名など）
- **リクエストパラメータ**: APIリクエストの詳細
- **レスポンス要素**: APIレスポンスの詳細

---

## よくある質問

### Q: WordsFunctionのログだけを表示したい

**A**: 方法3（IAMロール名で検索）が最も正確です。ただし、ロール名を事前に確認する必要があります。

### Q: WordsFunctionが実行した操作の回数を確認したい

**A**: 方法4を使用して、時間範囲を指定して検索し、結果の数をカウントします。

### Q: WordsFunctionのエラーを確認したい

**A**: 方法5のエラー検索コマンドを使用します。または、CloudTrailコンソールでレスポンスコードでフィルタします。

### Q: WordsFunction以外のLambda関数のログも表示されてしまう

**A**: これは正常です。DynamoDBテーブル名で検索した場合、そのテーブルにアクセスするすべてのLambda関数のログが表示されます。WordsFunctionだけを表示したい場合は、IAMロール名で検索してください。

---

## 参考

- [CloudTrail無料構成の実装ガイド](./CLOUDTRAIL_FREE_SETUP.md)
- [AWS CloudTrail イベント履歴](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html)
- [AWS CLI CloudTrail コマンド](https://docs.aws.amazon.com/cli/latest/reference/cloudtrail/index.html)


