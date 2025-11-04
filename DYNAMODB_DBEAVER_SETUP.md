# DBeaverでDynamoDBに接続する手順

このドキュメントでは、DBeaverを使用してDynamoDBテーブルを閲覧・編集する方法を説明します。

## 前提条件

1. **DBeaverのインストール**
   - [DBeaver公式サイト](https://dbeaver.io/download/)からDBeaverをダウンロードしてインストール
   
   **DBeaverのエディションについて**:
   - **Community Edition（コミュニティ版）**: 
     - ✅ **完全に無料**のオープンソース版
     - 基本的なデータベース接続機能が利用可能
     - DynamoDBへの直接接続機能は含まれていませんが、CData JDBCドライバーを使用することで接続可能（後述）
     - 個人利用や小規模プロジェクトに最適
   
   - **Enterprise Edition / Ultimate Edition / Team Edition**:
     - 有料版（サブスクリプション）
     - DynamoDBへの直接接続機能が標準で含まれています
     - 企業向けの追加機能やサポートが提供されます
   
   **重要**: DynamoDB接続は以下のエディションで標準サポートされています：
     - Enterprise Edition
     - Ultimate Edition
     - Team Edition
   
   **Community Edition（無料版）を使用する場合**: CData JDBCドライバーを使用する方法（後述）が必要です

2. **AWS認証情報の準備**
   - AWS Access Key ID
   - AWS Secret Access Key
   - これらの認証情報は、AWS IAMで適切な権限を持つユーザーから取得してください
   - 必要なIAM権限: `dynamodb:ListTables`, `dynamodb:DescribeTable`, `dynamodb:Scan`, `dynamodb:Query`, `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:DeleteItem`

## 接続情報

プロジェクトの設定から、以下の情報が必要です：

- **AWSリージョン**: `ap-northeast-1` (東京リージョン)
- **テーブル名**: `${AWS::StackName}-table` 
  - デフォルトでは `japanese-learn-table` が使用されます
  - 実際のテーブル名はAWSコンソールで確認してください

## DBeaverでの接続手順

### 方法1: Enterprise/Ultimate/Teamエディションを使用する場合（推奨）

DBeaverのEnterprise/Ultimate/Teamエディションには、DynamoDB接続機能が標準で含まれています。

1. **Database** → **New Database Connection** をクリック
2. **Amazon DynamoDB** を検索して選択
3. 接続情報を入力：
   - **Access Key ID**: AWS Access Key ID
   - **Secret Access Key**: AWS Secret Access Key
   - **Region**: `ap-northeast-1`
   - **Endpoint**: 空白のまま（デフォルトのエンドポイントを使用）
4. **Test Connection** をクリックして接続をテスト
5. 接続が成功したら **Finish** をクリック

### 方法2: Community EditionでCData JDBCドライバーを使用する場合

Community Editionを使用している場合は、CDataのJDBCドライバーを使用してDynamoDBに接続できます。

#### ステップ1: CData JDBCドライバーのダウンロード

1. [CData JDBC Driver for Amazon DynamoDB](https://www.cdata.com/drivers/dynamodb/jdbc/)にアクセス
2. 試用版をダウンロード（またはライセンスを購入）

#### ステップ2: DBeaverでのドライバー設定

1. DBeaverを起動
2. **Database** → **Driver Manager** を開く
3. **New Driver** をクリック
4. 以下の情報を入力：
   - **Driver Name**: `CData DynamoDB`
   - **Driver Type**: `Generic`
   - **Class Name**: `cdata.jdbc.dynamodb.DynamoDBDriver`
   - **URL Template**: `jdbc:dynamodb:AccessKey={accesskey};SecretKey={secretkey};Region={region};`
5. **Libraries** タブで、ダウンロードしたCData JDBCドライバーのJARファイルを追加
6. **OK** をクリック

#### ステップ3: 接続の作成

1. **Database** → **New Database Connection** をクリック
2. **CData DynamoDB** を選択
3. 接続情報を入力：
   - **JDBC URL**: `jdbc:dynamodb:AccessKey=<AccessKeyID>;SecretKey=<SecretAccessKey>;Region=ap-northeast-1;`
   - または、個別のフィールドに：
     - **Access Key**: AWS Access Key ID
     - **Secret Key**: AWS Secret Access Key
     - **Region**: `ap-northeast-1`
4. **Test Connection** をクリックして接続をテスト
5. 接続が成功したら **Finish** をクリック

**注意**: CData JDBCドライバーは有料ライセンスが必要な場合があります。試用版も利用可能です。

### 3. テーブルの確認（方法1、方法2共通）

接続後、左側のナビゲーションツリーから：
1. データベース接続を展開
2. **Tables** フォルダを展開
3. テーブル名（例: `japanese-learn-table`）を確認

### 4. データの閲覧

1. テーブルを右クリック → **View Data** を選択
2. または、SQL Editorで以下のようなクエリを実行：
   ```sql
   SELECT * FROM "japanese-learn-table" LIMIT 100
   ```

**注意**: DynamoDBはNoSQLデータベースのため、SQLクエリのサポートは限定的です。主なキー（PK、SK）での検索が中心となります。

## テーブル構造

このプロジェクトのDynamoDBテーブルは以下の構造です：

- **パーティションキー（PK）**: String (S)
- **ソートキー（SK）**: String (S)
- **グローバルセカンダリインデックス（GSI）**:
  - `word-level-index` (PK, level)
  - `name-index` (name)
  - `chinese-index` (chinese)
  - `korean-index` (korean)
  - `indonesian-index` (indonesian)
  - `hindi-index` (hindi)

## データの編集

DBeaverでDynamoDBのデータを編集する場合：

1. テーブルを開いてデータを表示
2. 行をダブルクリックして編集モードに入る
3. 値を変更
4. **Save** ボタンをクリックして保存

**注意**: DynamoDBの特性上、編集機能は限定的な場合があります。重要なデータを編集する前に、必ずバックアップを取ることを推奨します。

## トラブルシューティング

### 接続エラーが発生する場合

1. **AWS認証情報の確認**
   - Access Key IDとSecret Access Keyが正しいか確認
   - IAMユーザーにDynamoDBへのアクセス権限があるか確認

2. **リージョンの確認**
   - テーブルが存在するリージョンが正しいか確認（`ap-northeast-1`）

3. **ネットワーク設定**
   - ファイアウォールやプロキシ設定がAWSへの接続をブロックしていないか確認

### テーブルが表示されない場合

1. **テーブル名の確認**
   - AWSコンソールで実際のテーブル名を確認
   - テーブル名は `${StackName}-table` の形式です

2. **権限の確認**
   - IAMユーザーに `dynamodb:ListTables` 権限があるか確認

## AWS CLIでの確認方法

DBeaverで接続できない場合、AWS CLIでテーブルを確認できます：

```bash
# テーブル一覧の確認
aws dynamodb list-tables --region ap-northeast-1

# テーブル情報の確認
aws dynamodb describe-table --table-name <テーブル名> --region ap-northeast-1

# データの確認（サンプル）
aws dynamodb scan --table-name <テーブル名> --region ap-northeast-1 --limit 5
```

## 代替手段: AWS NoSQL Workbench

DBeaverが利用できない場合や、よりDynamoDBに特化したツールが必要な場合は、AWS公式の**NoSQL Workbench**も利用できます。

### NoSQL Workbenchのインストール

1. [AWS NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html)からダウンロード
2. インストール後、AWS認証情報を設定
3. 接続先のリージョンとテーブルを選択

### NoSQL Workbenchの特徴

- DynamoDB専用のGUIツール
- データの視覚的な設計・操作が可能
- サンプルデータの追加が容易
- ライブデータセットへの接続が可能
- 無料で利用可能

## 参考リンク

- [DBeaver公式ドキュメント - DynamoDB](https://dbeaver.com/docs/dbeaver/AWS-DynamoDB/)
- [AWS DynamoDBドキュメント](https://docs.aws.amazon.com/dynamodb/)
- [AWS CLI設定](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)
- [CData JDBC Driver for DynamoDB](https://www.cdata.com/drivers/dynamodb/jdbc/)
- [AWS NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html)

