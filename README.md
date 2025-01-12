# Japanese Learn API

日本語学習支援APIサービス

## 開発環境のセットアップ

### 必要条件
- Docker
- Docker Compose
- Make
- AWS CLI（デプロイ時のみ必要）
- Python 3.9以上

### 開発環境の起動

```bash
# 開発サーバーの起動（バックグラウンド実行）
make dev

# ログの確認
make logs

# 開発サーバーの停止
make down
```

開発サーバーは`http://localhost:8000`で起動します。
ソースコードを変更すると自動的に反映されます（ホットリロード）。

## AWS Lambdaへのデプロイ

### デプロイの準備

1. AWS CLIのインストールと設定
```bash
# AWS CLIのインストール（まだの場合）
pip install awscli

# AWS認証情報の設定
aws configure
# AWS Access Key ID: [アクセスキーを入力]
# AWS Secret Access Key: [シークレットキーを入力]
# Default region name: ap-northeast-1
# Default output format: json
```

2. Lambda関数の作成（初回のみ）
- AWSコンソールでLambda関数を作成
- 関数名: `japanese-learn-api`
- ランタイム: Python 3.9
- アーキテクチャ: x86_64

3. API Gatewayの設定
- REST APIを作成
- リソースとメソッドの設定
  - `/api/v1/words` にGETメソッドを追加
  - Lambdaプロキシ統合を選択
  - Lambda関数として`japanese-learn-api`を選択

4. メソッドレスポンスの設定（重要）
- API Gateway コンソールで各メソッドの設定を開く
- 「メソッドレスポンス」を選択
- 以下のステータスコードを追加：
  - 200
  - 400
  - 404
  - 500
- 200レスポンスに以下のレスポンスヘッダーを追加：
  - Content-Type
  - Access-Control-Allow-Origin

5. 統合レスポンスの設定
- 「統合レスポンス」を選択
- 各ステータスコードに対して以下を設定：

200レスポンスの設定：
```
レスポンスヘッダー:
- Content-Type: 'application/json'
- Access-Control-Allow-Origin: '*'

マッピングテンプレート:
Content-Type: application/json
テンプレート: $input.json('$.body')
```

400/404/500レスポンスの設定：
```
レスポンスヘッダー:
- Content-Type: 'application/json'
- Access-Control-Allow-Origin: '*'

マッピングテンプレート:
Content-Type: application/json
テンプレート: $input.json('$')
```

6. APIのデプロイ
- 「APIのデプロイ」を選択
- ステージを選択または新規作成
- デプロイを実行

### デプロイ手順

```bash
# デプロイの実行
make deploy
```

このコマンドは以下の処理を順番に実行します：
1. クリーンアップ（`make clean`）
2. ビルド（`make build`）
3. パッケージング（`make package`）
4. AWSへのアップロード（`make upload`）

## 利用可能なMakeコマンド

```bash
make help  # 使用可能なコマンドの一覧を表示

# 開発用コマンド
make dev   # 開発環境を起動
make down  # 開発環境を停止
make logs  # 開発環境のログを表示

# デプロイ用コマンド
make deploy   # デプロイを実行（clean, build, package, uploadを順番に実行）
make clean    # Pythonディレクトリをクリーンアップ
make build    # アプリケーションをビルド
make package  # Lambda用にパッケージング
make upload   # AWSにアップロード
```

## トラブルシューティング

### よくある問題と解決方法

1. API Gateway 500エラー
- メソッドレスポンスに必要なステータスコード（200, 400, 404, 500）が設定されているか確認
- 統合レスポンスの各ステータスコードに対するマッピングが正しく設定されているか確認
- Lambda関数のタイムアウト設定が適切か確認（推奨: 30秒以上）

2. Invalid Method Response エラー
- メソッドレスポンスを先に設定してから統合レスポンスを設定する
- 必要なレスポンスヘッダーがメソッドレスポンスに定義されているか確認

3. Lambda関数のエラー
- CloudWatchログで詳細なエラーメッセージを確認
- 環境変数が正しく設定されているか確認
- 必要なIAMロールとポリシーが設定されているか確認