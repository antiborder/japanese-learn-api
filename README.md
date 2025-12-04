# Japanese Learn API

日本語学習支援APIサービス

## 開発環境のセットアップ

### 必要条件
- Docker
- Docker Compose
- Make
- AWS CLI（デプロイ時のみ必要）
- Python 3.11以上

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

### ローカルでのuvicornを使ったテスト

個別のモジュールを直接テストする場合は、uvicornを使用できます：

```bash
# wordsモジュールのテスト例
cd /Users/mo/Projects/japanese-learn-api/app/api/v1/words
export PYTHONPATH="/Users/mo/Projects/japanese-learn-api/app/api/v1:$PYTHONPATH"
uvicorn app:app --reload --port 8000
```

**注意**: `PYTHONPATH`の設定が必要です。これは`common`ディレクトリ内の共通モジュール（設定、スキーマ、ユーティリティなど）を参照するために必要です。`PYTHONPATH`を設定しないと、インポートエラーが発生します。

各モジュール（words、kanjis、sentences、search、learn_words、sentence_composition、chat）で同様の方法でテストできます。

**chatモジュールのローカルテスト例**：
```bash
# chatモジュールのテスト
cd /Users/mo/Projects/japanese-learn-api/app/api/v1/chat
export PYTHONPATH="/Users/mo/Projects/japanese-learn-api/app/api/v1:$PYTHONPATH"
export GEMINI_API_KEY="your-gemini-api-key"
export DYNAMODB_TABLE_NAME="japanese-learn-table"
export FRONTEND_BASE_URL="http://localhost:3000"  # オプション（デフォルト値あり）
export CONVERSATION_LOGS_TABLE_NAME="chat-conversations"  # オプション（Phase 2で使用）
uvicorn app:app --reload --port 8000
```

curl コマンドの例：
```bash
# チャットボットのテスト
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What does こんにちは mean?", "session_id": "test-session-123"}'

# 他のエンドポイントのテスト例
curl http://localhost:8000/api/v1/kanjis/101/ai-explanation
```

## デプロイ後のテスト

curlコマンドの例
```bash
curl https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/kanjis/101/ai-explanation
```

## コードスタイルガイドライン

### Import文の書き方ルール

このアプリケーションでは、以下のimport文のルールに従ってください：

#### 1. 絶対importの使用を推奨
- **相対import（`from .module`）は避ける**: コードの可読性と保守性を向上させるため
- **絶対importを使用**: `from common.schemas.word import Word` のように、モジュールの完全パスを指定
- schemaはcommonに記述。

#### 2. Import文の順序
```python
# 1. 標準ライブラリ
import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

# 2. サードパーティライブラリ
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3

# 3. アプリケーション内のモジュール（絶対import）
from common.schemas.word import Word, WordKanji
from common.utils.utils import convert_hiragana_to_romaji
from services.word_service import get_audio_url
from integrations.dynamodb_integration import dynamodb_client
```

#### 3. 相対importの使用例（限定的な使用）
相対importは以下の場合のみ使用：
- 同一ディレクトリ内のモジュール間の参照
- `__init__.py`でのモジュールの再エクスポート

```python
# 同一ディレクトリ内での相対import（許容される）
from .datetime_service import DateTimeService
from .base import DynamoDBBase

# 絶対importが推奨される
from common.schemas.word import Word
from services.word_service import get_audio_url
```

#### 4. なぜ相対importを避けるべきか
- **可読性**: モジュールの依存関係が明確になる
- **保守性**: ファイルの移動やリネーム時の影響を最小化
- **デバッグ**: エラーの原因を特定しやすい
- **テスト**: 個別モジュールのテストが容易

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
- ランタイム: Python 3.11
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

## 本番環境デプロイ前のチェック項目

### 必須チェック項目

デプロイ前に以下の項目を必ず確認してください：

1. **環境変数の設定確認**
   - 各Lambda関数に必要な環境変数が設定されているか確認
   - 特に以下の環境変数が不足していないかチェック：
     - `GEMINI_API_KEY`: AI解説機能に必要
     - `S3_BUCKET_NAME`: S3操作に必要
     - `AWS_REGION`: AWS操作に必要
   - 環境変数が設定されていない場合、API呼び出し時に500エラーが発生する

2. **パッケージ依存関係の確認**
   - 各Lambda関数の`requirements.txt`に必要なパッケージが含まれているか確認
   - ローカルで使うrequiremtents.txtはルートにあるが、lambdaで使うrequirements.txtは各ラムダのフォルダにある。
   - 特に新機能追加時に以下のパッケージが不足していないかチェック：
     - `google-generativeai`: AI解説機能に必要
     - `boto3`: AWS操作に必要
     - `fastapi`: API機能に必要
   - パッケージが不足している場合、Lambda関数のインポートエラーが発生する

3. **IAMロールとポリシーの確認**
   - Lambda関数に必要なAWS権限が設定されているか確認
   - S3、DynamoDB、CloudWatch Logsへのアクセス権限が適切に設定されているか確認
   
4. **makefileの確認**
   - 他のlambdaのコードを参考にして、不足がないか確認

5. **template.yamlの確認**
   - 他のlambdaの設定を参考にして、不足がないか確認

### チェック方法

```bash
# 環境変数の確認
aws lambda get-function-configuration --function-name japanese-learn-SentencesFunction --query "Environment.Variables"

# パッケージの確認（ローカルで）
pip list | grep google-generativeai
pip list | grep boto3
```

## DynamoDBへのデータimport

```bash
# venv環境へ入る。
source venv/bin/activate

# word-kanji mappingの作成
# data/word_kanji_XXXXXXXX.csvとdata/kanji_word_XXXXXXXX.csvが作成される
python3 scripts/create_word_kanji_mapping.py

# wordsのimport
python3 scripts/import_dynamodb.py

# sentencesのimport
python3 scripts/import_sentences_to_dynamodb.py
```


## 言語の追加
1. data/dynamodb_sourceのwordsとsentencesのcsvに、対象言語のカラムを足して、import
2. LanguageEnumへ言語を追加。
3. バックエンドのschemaとapiでの戻り値に対象言語を追加。words/[id],sentences/[id],next,next/randomなど。
4. 漢字AI解説の見出しを新言語分追加


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

4. 環境変数不足エラー
- `"GEMINI_API_KEY not found in environment variables"`エラーが発生した場合
- 該当するLambda関数の環境変数に`GEMINI_API_KEY`を設定する
- AWS LambdaコンソールまたはAWS CLIで環境変数を追加

5. パッケージ不足エラー
- `"No module named 'google.generativeai'"`エラーが発生した場合
- 該当するLambda関数の`requirements.txt`に`google-generativeai==0.8.5`を追加
- パッケージを再デプロイする