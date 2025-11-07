# CloudTrail無料構成の実装ガイド

## 概要

CloudTrailの無料構成では、**S3バケットへの配信を行わず**、CloudTrailコンソールで直接イベント履歴を閲覧します。この構成では、**追加コストは一切発生しません**。

## ⚠️ 重要な注意事項

### CloudTrailイベント履歴はアカウント全体のデフォルト機能

**重要**: CloudTrailのイベント履歴は、**このアプリケーション専用ではなく、AWSアカウント全体のデフォルト機能**です。

- **アカウント全体のログ**: 同じAWSアカウント内のすべてのアプリケーション・サービスのログが混在します
- **他のアプリのログも含まれる**: 同じアカウントで実行されている他のアプリケーションのログも一緒に表示されます
- **すべてのAWSサービスのログ**: EC2、RDS、S3、Lambda、DynamoDB、その他すべてのAWSサービスの管理イベントが記録されます
- **フィルタリングが必要**: この日本語学習アプリのログだけを見るには、適切なフィルタリングが必要です

### 記録されるサービスの例

CloudTrailのイベント履歴には、以下のような**すべてのAWSサービス**の管理イベントが記録されます：

- ✅ **EC2**: インスタンスの起動・停止、セキュリティグループの変更など
- ✅ **RDS**: データベースの作成・削除、スナップショットの作成など
- ✅ **S3**: バケットの作成・削除、バケットポリシーの変更など
- ✅ **Lambda**: 関数の作成・更新・削除、設定の変更など
- ✅ **DynamoDB**: テーブルの作成・削除、API呼び出し（PutItem、Queryなど）など
- ✅ **IAM**: ユーザーの作成・削除、ポリシーの変更など
- ✅ **その他すべてのAWSサービス**: CloudFormation、API Gateway、Cognitoなど

### このアプリのリソースを識別する方法

このアプリケーションのリソースは以下の命名規則で識別できます：

- **スタック名**: `japanese-learn`
- **DynamoDBテーブル**: `japanese-learn-table`
- **Lambda関数**: 
  - `japanese-learn-WordsFunction`
  - `japanese-learn-LearnWordsFunction`
  - `japanese-learn-UsersFunction`
  - `japanese-learn-KanjisFunction`
  - `japanese-learn-SearchFunction`
  - `japanese-learn-SentencesFunction`
  - `japanese-learn-SentenceCompositionFunction`

### 無料構成の特徴

✅ **完全無料**: 月額 $0 / 月  
✅ **90日間のイベント履歴**: 直近90日間の管理イベントを記録・検索可能  
✅ **簡単設定**: 追加のリソース（S3バケットなど）不要  
✅ **リアルタイム監視**: CloudTrailコンソールで即座にイベントを確認可能  
✅ **アカウント全体の監視**: すべてのAWSサービスの管理イベントを監視可能  

### 制限事項

❌ **アカウント全体のログ**: このアプリ専用ではなく、アカウント全体のログが混在  
❌ **フィルタリング必須**: このアプリのログだけを見るには、適切なフィルタリングが必要  
❌ **90日を超えたログは保持されない**: 90日を超えたログは自動的に削除されます  
❌ **データイベントは記録されない**: 管理イベントのみ記録（GetItem、Queryなどの詳細なデータ操作は記録されない）  
❌ **プログラムからのアクセス制限**: CloudTrailコンソールからの閲覧が主な方法  
❌ **長期保存不可**: S3への配信が必要な場合は、有料オプションが必要  

---

## 無料構成の仕組み

### イベント履歴（Event History）

CloudTrailは、**デフォルトでAWSアカウント全体の管理イベントを記録**しています。これは追加の設定なしで利用できます。

- **記録されるイベント**: 
  - **DynamoDB**: テーブル作成・削除、API呼び出し（PutItem, Query, UpdateItemなど）
  - **EC2**: インスタンスの起動・停止、セキュリティグループの変更、AMIの作成など
  - **RDS**: データベースの作成・削除、スナップショットの作成、パラメータグループの変更など
  - **S3**: バケットの作成・削除、バケットポリシーの変更など
  - **Lambda**: 関数の作成・更新・削除、設定の変更など
  - **IAM**: ユーザーの作成・削除、ポリシーの変更、ロールの変更など
  - **CloudFormation**: スタックの作成・更新・削除など
  - **その他のすべてのAWSサービス**: API Gateway、Cognito、CloudWatch、その他すべてのAWSサービスの管理操作

- **記録されないイベント**:
  - データレベルの操作の詳細（GetItem, Query, PutItem の詳細内容）
  - データイベント（詳細なデータ操作）

### 無料枠の内容

- **管理イベントの最初のコピー**: 無料
- **90日間の保持**: 無料
- **CloudTrailコンソールでの検索**: 無料
- **イベントのダウンロード**: 無料（最大100件）

---

## 実装方法

### 方法1: AWSコンソールから手動設定（推奨・最も簡単）

#### ステップ1: CloudTrailコンソールを開く

1. AWSマネジメントコンソールにログイン
2. 「CloudTrail」サービスを検索して開く
3. 左側のメニューから「イベント履歴（Event history）」を選択

#### ステップ2: イベント履歴の確認

- **デフォルトで有効**: イベント履歴はデフォルトで有効になっています
- **追加設定不要**: 特別な設定は不要です
- **すぐに利用可能**: すぐにイベントを確認できます

#### ステップ3: イベントの検索とフィルタリング（重要：このアプリのログだけを表示）

**このアプリケーションのログだけを表示するには、適切なフィルタリングが必要です。**

1. **時間範囲の指定**: 
   - 過去90日間の任意の期間を選択
   
2. **フィルタリング（このアプリ専用）**:
   
   **方法A: リソース名でフィルタ（推奨）**
   ```
   リソース名: japanese-learn-table
   ```
   - このアプリのDynamoDBテーブルに関連するすべてのイベントを表示
   
   **方法B: イベント名とリソース名の組み合わせ**
   ```
   イベント名: dynamodb:PutItem
   リソースタイプ: AWS::DynamoDB::Table
   リソース名: japanese-learn-table
   ```
   - このアプリのテーブルへのPutItem操作のみを表示
   
   **方法C: Lambda関数名でフィルタ**
   ```
   リソース名: japanese-learn-*
   ```
   - このアプリのすべてのLambda関数に関連するイベントを表示
   - 注意: ワイルドカードが使えない場合は、個別に関数名を指定

3. **このアプリのDynamoDBイベントの検索例**:
   ```
   リソース名: japanese-learn-table
   リソースタイプ: AWS::DynamoDB::Table
   ```
   
4. **このアプリのLambda関数のイベントの検索例**:
   ```
   リソース名: japanese-learn-LearnWordsFunction
   または
   リソース名: japanese-learn-WordsFunction
   など
   ```

**⚠️ 注意**: フィルタリングを設定しないと、**アカウント内のすべてのアプリケーションのログが表示**されます。EC2、RDS、S3、その他のAWSサービスのログも一緒に表示されるため、このアプリのログだけを見るにはフィルタリングが必須です。

---

### 方法2: CloudFormation/SAMテンプレートでの設定（オプション）

S3配信なしのCloudTrailをCloudFormationで明示的に設定する場合の例：

```yaml
  # CloudTrail（無料構成：イベント履歴のみ、S3配信なし）
  CloudTrailEventHistory:
    Type: AWS::CloudTrail::Trail
    Properties:
      TrailName: !Sub "${AWS::StackName}-event-history"
      # S3BucketNameを指定しない = S3への配信なし（無料）
      IncludeGlobalServiceEvents: true
      IsLogging: true
      IsMultiRegionTrail: false
      # 管理イベントのみ記録（データイベントは記録しない = コスト削減）
      EventSelectors:
        - ReadWriteType: All
          IncludeManagementEvents: true
          ExcludeManagementEventSources: []
      # ログファイルの検証を有効化（セキュリティ向上）
      EnableLogFileValidation: true
      Tags:
        - Key: Purpose
          Value: EventHistory
        - Key: Environment
          Value: !Ref AWS::StackName
        - Key: Cost
          Value: Free
```

**注意**: 
- S3バケットを指定しない場合、イベント履歴のみが記録されます
- この構成でも、CloudTrailコンソールで90日間のイベントを確認できます
- **ただし、実はCloudTrailはデフォルトでイベント履歴を記録しているため、このリソースは必ずしも必要ではありません**

---

## イベントの確認方法

### CloudTrailコンソールでの確認

#### 1. イベント履歴の閲覧

```
AWS Console → CloudTrail → イベント履歴
```

#### 2. このアプリのDynamoDB関連のイベントを検索

**⚠️ 注意**: デフォルトでは、アカウント内のすべてのアプリケーションのログが表示されます。このアプリのログだけを見るには、フィルタリングが必要です。

**検索例1: このアプリのテーブルへのすべての操作を確認**
```
リソース名: japanese-learn-table
```
これにより、このアプリのDynamoDBテーブルに関連するイベントのみが表示されます。

**検索例2: このアプリのテーブルへの書き込み操作を確認**
```
イベント名: dynamodb:PutItem
リソース名: japanese-learn-table
```
または
```
イベント名: dynamodb:UpdateItem
リソース名: japanese-learn-table
```

**検索例3: このアプリのテーブルへの削除操作を確認**
```
イベント名: dynamodb:DeleteItem
リソース名: japanese-learn-table
```

**検索例4: このアプリのテーブルへの読み取り操作を確認**
```
イベント名: dynamodb:Query
リソース名: japanese-learn-table
```
または
```
イベント名: dynamodb:GetItem
リソース名: japanese-learn-table
```

**検索例5: このアプリのLambda関数に関連するイベントを確認**
```
リソース名: japanese-learn-LearnWordsFunction
```
特定のLambda関数のイベントのみを表示します。

**検索例6: 他のアプリのリソースを除外して確認（例: EC2のイベント）**
```
イベント名: RunInstances
リソースタイプ: AWS::EC2::Instance
```
フィルタリングしないと、アカウント内のすべてのEC2インスタンスの起動イベントが表示されます。

#### 3. イベントの詳細を確認

各イベントをクリックすると、以下の情報が表示されます：
- **イベント時間**: イベントが発生した日時
- **ユーザー名**: イベントを実行したユーザーまたはロール
- **イベント名**: 実行されたAPI操作（例: `PutItem`, `Query`）
- **リソース名**: 操作対象のリソース
- **イベントID**: イベントの一意識別子
- **リクエストパラメータ**: APIリクエストの詳細（一部）
- **レスポンス要素**: APIレスポンスの詳細（一部）

---

### AWS CLIでの確認

**このアプリのログだけを表示するには、リソース名でフィルタリングします。**

```bash
# このアプリのDynamoDBテーブルに関連するイベントを検索（推奨）
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100

# 過去7日間のこのアプリのテーブルへのイベントを検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 100

# このアプリのテーブルへのPutItem操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=PutItem \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100

# このアプリのLambda関数に関連するイベントを検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-LearnWordsFunction \
  --max-results 100

# このアプリのテーブルへの削除操作を検索（セキュリティ監視）
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=DeleteItem \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 1000
```

**⚠️ 注意**: フィルタリングを設定しないと、アカウント内のすべてのアプリケーションのログが返されます。EC2、RDS、S3などの他のサービスのログも含まれるため、このアプリのログだけを見るにはフィルタリングが必須です。

**例: フィルタリングなしの場合（すべてのログが表示される）**
```bash
# フィルタリングなし = アカウント全体のログが表示される
aws cloudtrail lookup-events --max-results 100
# 結果: EC2、RDS、S3、DynamoDB、Lambda、その他すべてのAWSサービスのログが混在
```

---

## 実用例：このアプリのDynamoDBアクセスの監査

### シナリオ1: このアプリの異常なアクセスパターンの検出

**目的**: このアプリのテーブルへの大量の削除操作が発生していないか確認

```bash
# 過去24時間のこのアプリのテーブルへのDeleteItem操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=DeleteItem \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 1000
```

### シナリオ2: このアプリのLambda関数の操作履歴を確認

**目的**: このアプリのLambda関数が実行したDynamoDB操作を確認

```bash
# このアプリのLearnWordsFunctionが実行した操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-LearnWordsFunction \
  --max-results 100

# または、このアプリのテーブルへの操作で、Lambda関数のロールをフィルタ
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
    AttributeKey=Username,AttributeValue=arn:aws:sts::123456789012:assumed-role/japanese-learn-LearnWordsFunctionRole-XXXXX/session \
  --max-results 100
```

### シナリオ3: このアプリのテーブル作成・削除の監視

**目的**: このアプリのインフラストラクチャの変更を監視

```bash
# このアプリのテーブルの作成を検索
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=CreateTable \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100

# このアプリのテーブルの削除を検索
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=DeleteTable \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100
```

### シナリオ4: このアプリのすべてのDynamoDB操作を一括確認

**目的**: このアプリのテーブルへのすべての操作を確認

```bash
# このアプリのテーブルに関連するすべてのイベントを検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 1000
```

### シナリオ5: WordsFunctionのLambda関数のログを検索（実用例）

**目的**: WordsFunctionが実行したすべての操作を確認

#### 方法1: Lambda関数のリソース名で検索

```bash
# WordsFunctionに関連するすべてのイベントを検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-WordsFunction \
  --max-results 100
```

**結果**: 
- Lambda関数の作成・更新・削除などの管理イベント
- Lambda関数の設定変更イベント

#### 方法2: WordsFunctionが実行したDynamoDB操作を検索

WordsFunctionはDynamoDBに対して以下の操作を行います：
- `Query`: 単語一覧の取得
- `GetItem`: 特定の単語の取得

```bash
# WordsFunctionが実行したQuery操作を検索
# （このアプリのテーブルへのQuery操作で、WordsFunctionのロールから実行されたもの）
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=Query \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100

# WordsFunctionが実行したGetItem操作を検索
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=GetItem \
    AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100
```

#### 方法3: Lambda関数のロール名で検索（より正確）

WordsFunctionが使用するIAMロール名から検索する方法：

```bash
# まず、WordsFunctionのロール名を確認（実際のロール名に置き換える）
# ロール名の形式: japanese-learn-WordsFunctionRole-XXXXX

# ロール名で検索（実行ロールから実行された操作を検索）
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=arn:aws:sts::YOUR_ACCOUNT_ID:assumed-role/japanese-learn-WordsFunctionRole-XXXXX/* \
  --max-results 100
```

**注意**: `YOUR_ACCOUNT_ID` と `XXXXX` は実際の値に置き換えてください。

#### 方法4: 過去24時間のWordsFunctionの操作を確認

```bash
# 過去24時間のこのアプリのテーブルへの操作を検索
# （WordsFunctionが実行した可能性が高い）
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 1000 \
  | grep -i "WordsFunction\|Query\|GetItem"
```

#### CloudTrailコンソールでの検索方法

1. **CloudTrailコンソールを開く**
   - AWS Console → CloudTrail → イベント履歴

2. **フィルタリング設定**:
   - **リソース名**: `japanese-learn-WordsFunction`
   - または
   - **イベント名**: `Query` または `GetItem`
   - **リソース名**: `japanese-learn-table`

3. **時間範囲**: 過去7日間または過去24時間を選択

#### WordsFunctionが記録されるイベントの例

- ✅ **Lambda関数の管理イベント**:
  - `CreateFunction`: 関数の作成
  - `UpdateFunctionCode`: コードの更新
  - `UpdateFunctionConfiguration`: 設定の更新
  - `DeleteFunction`: 関数の削除

- ✅ **DynamoDB操作**:
  - `Query`: 単語一覧の取得（`get_words()`）
  - `GetItem`: 特定の単語の取得（`get_word_by_id()`）
  - `Query`: 単語に関連する漢字の取得（`get_kanjis_by_word_id()`）

- ✅ **S3操作**（WordsFunctionもS3を使用）:
  - `PutObject`: 音声ファイルや画像の保存
  - `GetObject`: 音声ファイルや画像の取得
  - `ListBucket`: バケットの一覧取得

#### 実用的な検索コマンド例

```bash
# WordsFunctionに関連するすべてのイベント（過去7日間）
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-WordsFunction \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 500

# WordsFunctionが実行したDynamoDB操作（過去24時間）
aws cloudtrail lookup-events \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --max-results 1000 \
  | jq '.Events[] | select(.Resources[]?.ResourceName == "japanese-learn-table" or .Resources[]?.ResourceName == "japanese-learn-WordsFunction")'

# WordsFunctionのエラーを確認（DynamoDBエラーなど）
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=japanese-learn-table \
  --max-results 100 \
  | jq '.Events[] | select(.CloudTrailEvent | contains("error") or contains("Error") or contains("exception"))'
```

---

### 参考: 他のアプリのログも確認できる例

**EC2インスタンスの起動イベントを確認**（このアプリとは無関係）:
```bash
# アカウント内のすべてのEC2インスタンスの起動イベントを検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RunInstances \
  --max-results 100
```

**RDSデータベースの作成イベントを確認**（このアプリとは無関係）:
```bash
# アカウント内のすべてのRDSデータベースの作成イベントを検索
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateDBInstance \
  --max-results 100
```

これらは、このアプリとは無関係な、アカウント内の他のアプリケーションやサービスのログも表示されます。

---

## 無料構成のメリット・デメリット

### メリット

✅ **完全無料**: 追加コストが発生しない  
✅ **簡単設定**: デフォルトで有効、追加設定不要  
✅ **リアルタイム監視**: 即座にイベントを確認可能  
✅ **検索機能**: 90日間のイベントを柔軟に検索  
✅ **十分な監査**: 管理イベントで十分な監査が可能  

### デメリット

❌ **アカウント全体のログ**: このアプリ専用ではなく、アカウント全体のログが混在  
❌ **フィルタリング必須**: このアプリのログだけを見るには、適切なフィルタリングが必要  
❌ **90日間のみ保持**: 90日を超えたログは削除される  
❌ **データイベントなし**: 詳細なデータ操作は記録されない  
❌ **長期保存不可**: 長期保存が必要な場合はS3配信が必要  
❌ **プログラムアクセス制限**: CloudTrailコンソールやCLIでの検索が主な方法  

---

## 無料構成から有料構成への移行

将来的に、以下の要件が出てきた場合は、S3配信を有効化することを検討してください：

### 移行が必要なケース

1. **このアプリのログだけを分離したい**
2. **90日を超えたログの保存が必要**
3. **データイベントの詳細な記録が必要**（GetItem、Queryの詳細内容など）
4. **プログラムからの自動分析が必要**（S3ログを分析するLambda関数など）
5. **コンプライアンス要件**（7年間のログ保存など）

### 移行手順

1. S3バケットを作成
2. CloudTrailでS3配信を有効化
3. このアプリのリソースのみを記録するように設定
4. 既存のイベント履歴はそのまま利用可能
5. 新しいイベントはS3にも保存されるようになる

詳細は、`COST_ESTIMATE_CLOUDTRAIL_KMS.md`の「CloudTrail（S3配信あり）」を参照してください。

---

## このアプリ専用のCloudTrail証跡を作成する方法（有料オプション）

無料のイベント履歴はアカウント全体のログが混在しますが、**このアプリ専用のCloudTrail証跡を作成**することで、このアプリのログだけを分離できます。

### このアプリ専用のCloudTrail証跡のメリット

✅ **ログの分離**: このアプリのログだけが記録される  
✅ **長期保存**: 90日を超えたログも保存可能（S3に保存）  
✅ **プログラムからの分析**: S3に保存されたログを自動分析可能  
✅ **データイベントの記録**: 詳細なデータ操作も記録可能（オプション）  

### 実装方法

`template.yaml`に以下を追加：

```yaml
  # CloudTrail用S3バケット（このアプリ専用）
  CloudTrailLogsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${AWS::StackName}-cloudtrail-logs-${AWS::AccountId}"
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldLogs
            Status: Enabled
            ExpirationInDays: 90
      Tags:
        - Key: Purpose
          Value: CloudTrailLogs
        - Key: Application
          Value: japanese-learn

  # CloudTrail用S3バケットポリシー
  CloudTrailLogsBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref CloudTrailLogsBucket
      PolicyDocument:
        Statement:
          - Sid: AWSCloudTrailAclCheck
            Effect: Allow
            Principal:
              Service: cloudtrail.amazonaws.com
            Action: s3:GetBucketAcl
            Resource: !Sub "arn:aws:s3:::${CloudTrailLogsBucket}"
            Condition:
              StringEquals:
                "AWS:SourceArn": !Sub "arn:aws:cloudtrail:${AWS::Region}:${AWS::AccountId}:trail/${AWS::StackName}-trail"
          - Sid: AWSCloudTrailWrite
            Effect: Allow
            Principal:
              Service: cloudtrail.amazonaws.com
            Action: s3:PutObject
            Resource: !Sub "arn:aws:s3:::${CloudTrailLogsBucket}/*"
            Condition:
              StringEquals:
                "s3:x-amz-acl": bucket-owner-full-control
                "AWS:SourceArn": !Sub "arn:aws:cloudtrail:${AWS::Region}:${AWS::AccountId}:trail/${AWS::StackName}-trail"

  # CloudTrail証跡（このアプリ専用）
  CloudTrail:
    Type: AWS::CloudTrail::Trail
    Properties:
      TrailName: !Sub "${AWS::StackName}-trail"
      S3BucketName: !Ref CloudTrailLogsBucket
      IncludeGlobalServiceEvents: false  # グローバルサービスイベントを除外
      IsLogging: true
      IsMultiRegionTrail: false
      # このアプリのリソースに関連するイベントのみ記録
      EventSelectors:
        - ReadWriteType: All
          IncludeManagementEvents: true
          ExcludeManagementEventSources: []
          # このアプリのDynamoDBテーブルのみ記録
          DataResources:
            - Type: AWS::DynamoDB::Table
              Values:
                - !Sub "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}"
      EnableLogFileValidation: true
      Tags:
        - Key: Purpose
          Value: AuditLogging
        - Key: Application
          Value: japanese-learn
        - Key: Environment
          Value: !Ref AWS::StackName
```

### コスト

- **S3ストレージ**: 約 $0.023 / GB / 月
- **CloudTrailイベント**: 最初の90日間無料、その後 $2 / 100,000イベント
- **このアプリのみ記録**: 他のアプリのログは含まれないため、コストを削減

詳細は、`COST_ESTIMATE_CLOUDTRAIL_KMS.md`を参照してください。

---

## ベストプラクティス

### 1. 定期的な監視

- **週次レビュー**: 週に1回、異常な操作がないか確認
- **アラート設定**: CloudWatchアラームで異常な操作を検知（有料オプション）
- **ログ分析**: 定期的にイベント履歴を分析してパターンを把握

### 2. セキュリティ監視

- **削除操作の監視**: DeleteItem、DeleteTableなどの削除操作を重点的に監視
- **権限変更の監視**: IAMポリシーの変更を監視
- **異常なアクセスパターンの検出**: 通常と異なるアクセスパターンを検出

### 3. コスト管理

- **無料枠の活用**: 無料構成で十分な場合は、S3配信を有効化しない
- **必要に応じて移行**: 要件が変わったら、有料構成に移行

---

## トラブルシューティング

### イベントが表示されない

**原因**:
- イベントが発生していない
- 検索条件が厳しすぎる
- 90日を超えている

**解決方法**:
- 検索条件を緩和
- 時間範囲を確認
- 実際にAPI操作を実行してイベントが記録されるか確認

### 特定のイベントが見つからない

**原因**:
- データイベントは記録されない（無料構成では管理イベントのみ）
- イベント名のスペルミス
- リソース名の不一致

**解決方法**:
- 管理イベントのみ記録されることを確認
- イベント名を正確に入力
- ワイルドカードを使用（例: `dynamodb:*`）

---

## まとめ

### 無料構成の特徴

| 項目 | 詳細 |
|------|------|
| **コスト** | $0 / 月（完全無料） |
| **保持期間** | 90日間 |
| **記録されるイベント** | 管理イベントのみ |
| **対象範囲** | **AWSアカウント全体**（このアプリ専用ではない） |
| **フィルタリング** | **必須**（このアプリのログだけを見るには） |
| **アクセス方法** | CloudTrailコンソール、AWS CLI |
| **設定** | デフォルトで有効（追加設定不要） |

### 重要なポイント

1. **アカウント全体のログ**: 無料のイベント履歴は、AWSアカウント全体のログが混在します
2. **フィルタリング必須**: このアプリのログだけを見るには、リソース名（`japanese-learn-table`など）でフィルタリングが必要です
3. **他のサービスのログも含まれる**: EC2、RDS、S3、その他のAWSサービスのログも一緒に表示されます
4. **このアプリ専用が必要な場合**: アプリ専用のCloudTrail証跡を作成することを検討（有料オプション）

### 推奨事項

1. **初期段階**: 無料構成から開始し、リソース名でフィルタリング
2. **監視**: 定期的にこのアプリのイベント履歴を確認（フィルタリングを忘れずに）
3. **要件に応じて移行**: 
   - このアプリのログだけを分離したい場合
   - 90日を超えた保存が必要になったら
   - → S3配信を有効化し、このアプリ専用のCloudTrail証跡を作成

### 次のステップ

- CloudTrailコンソールでイベント履歴を確認
- 定期的な監視フローを確立
- 必要に応じて、S3配信を有効化

---

## 参考リンク

- [AWS CloudTrail イベント履歴](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html)
- [AWS CloudTrail 料金](https://aws.amazon.com/jp/cloudtrail/pricing/)
- [AWS CloudTrail ユーザーガイド](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html)

