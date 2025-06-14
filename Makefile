.PHONY: deploy clean build check-env check-aws-env check-db-env check-deps check-structure backup verify help rollback setup-aws dev-setup prepare-build clean-common

# デフォルトターゲット
.DEFAULT_GOAL := help

# シェルの設定
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# デプロイ（全ステップを実行）
deploy: check-env check-deps check-structure prepare-build build setup-aws
	@echo "デプロイを実行します..."
	@echo "SAMのバージョンを確認しています..."
	@sam --version
	@echo "デプロイ開始..."
	sam deploy \
		--stack-name japanese-learn \
		--s3-bucket aws-sam-cli-managed-default-samclisourcebucket-wifzlstdcfi8 \
		--parameter-overrides \
		DatabaseUrl="$$DATABASE_URL" \
		MaxComponentCount="$$MAX_COMPONENT_COUNT" \
		MinColumnCount="$$MIN_COLUMN_COUNT" \
		S3BucketName="$$S3_BUCKET_NAME" \
		GoogleCredentials="$$GOOGLE_APPLICATION_CREDENTIALS" \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--no-progressbar \
		|| { echo "デプロイに失敗しました。"; exit 1; }
	@echo "デプロイが完了しました"
	@make verify
	@make clean-common
	@make clean

# 開発用のセットアップ
dev-setup:
	@echo "開発環境をセットアップしています..."
	@for dir in words kanjis; do \
		echo "$$dirのPYTHONPATHを設定するには:"; \
		echo "export PYTHONPATH=/Users/mo/Projects/japanese-learn-api/app/api/v1/$$dir:\$$PYTHONPATH"; \
	done

# 環境チェック
check-env: check-aws-env check-db-env

# AWS環境チェック
check-aws-env:
	@echo "AWS環境を確認しています..."
	@command -v sam >/dev/null 2>&1 || { echo "Error: SAMがインストールされていません"; exit 1; }
	@command -v aws >/dev/null 2>&1 || { echo "Error: AWS CLIがインストールされていません"; exit 1; }
	@test -n "$$CUSTOM_AWS_ACCESS_KEY" || { echo "Error: CUSTOM_AWS_ACCESS_KEYが設定されていません"; exit 1; }
	@test -n "$$CUSTOM_AWS_SECRET_KEY" || { echo "Error: CUSTOM_AWS_SECRET_KEYが設定されていません"; exit 1; }
	@test -n "$$CUSTOM_AWS_REGION" || { echo "Error: CUSTOM_AWS_REGIONが設定されていません"; exit 1; }

# データベース環境変数チェック
check-db-env:
	@echo "データベース環境変数を確認しています..."
	@test -n "$$DATABASE_URL" || { echo "Error: DATABASE_URLが設定されていません"; exit 1; }
	@echo "$$DATABASE_URL" | grep -q "^mysql+pymysql://" || { echo "Error: DATABASE_URLの形式が正しくありません"; exit 1; }
	@test -n "$$MAX_COMPONENT_COUNT" || { echo "Error: MAX_COMPONENT_COUNTが設定されていません"; exit 1; }
	@echo "$$MAX_COMPONENT_COUNT" | grep -q "^[0-9][0-9]*$$" || { echo "Error: MAX_COMPONENT_COUNTは数値である必要があります"; exit 1; }
	@test -n "$$MIN_COLUMN_COUNT" || { echo "Error: MIN_COLUMN_COUNTが設定されていません"; exit 1; }
	@echo "$$MIN_COLUMN_COUNT" | grep -q "^[0-9][0-9]*$$" || { echo "Error: MIN_COLUMN_COUNTは数値である必要があります"; exit 1; }
	@test -n "$$S3_BUCKET_NAME" || { echo "Error: S3_BUCKET_NAMEが設定されていません"; exit 1; }
	@test -n "$$GOOGLE_APPLICATION_CREDENTIALS" || { echo "Error: GOOGLE_APPLICATION_CREDENTIALSが設定されていません"; exit 1; }
	@test -f "$$GOOGLE_APPLICATION_CREDENTIALS" || { echo "Error: Google認証ファイルが見つかりません: $$GOOGLE_APPLICATION_CREDENTIALS"; exit 1; }
	@python -c "import json; json.load(open('$$GOOGLE_APPLICATION_CREDENTIALS'))" 2>/dev/null || { echo "Error: Google認証ファイルが有効なJSONではありません"; exit 1; }

# 依存関係チェック
check-deps:
	@echo "依存関係を確認しています..."
	@for dir in app/api/v1/words app/api/v1/kanjis app/api/v1/learn_words; do \
		if [ ! -f $$dir/requirements.txt ]; then \
			echo "Error: $$dir/requirements.txtが見つかりません"; \
			exit 1; \
		fi; \
		if [ ! -f $$dir/requirements-dev.txt ]; then \
			echo "Error: $$dir/requirements-dev.txtが見つかりません"; \
			exit 1; \
		fi; \
		echo "$$dirの依存関係を確認中..."; \
		if ! pip install -r $$dir/requirements.txt --quiet --no-deps --dry-run >/dev/null 2>&1; then \
			echo "Error: $$dirのLambda用依存関係に問題があります"; \
			exit 1; \
		fi; \
		if ! pip install -r $$dir/requirements-dev.txt --quiet --no-deps --dry-run >/dev/null 2>&1; then \
			echo "Error: $$dirの開発用依存関係に問題があります"; \
			exit 1; \
		fi; \
	done

# ファイル構造チェック
check-structure:
	@echo "ファイル構造を確認しています..."
	@if [ ! -d "app/api/v1/common" ]; then \
		echo "Error: app/api/v1/commonディレクトリが見つかりません"; \
		exit 1; \
	fi
	@for file in config.py database.py; do \
		if [ ! -f "app/api/v1/common/$$file" ]; then \
			echo "Error: app/api/v1/common/$$fileが見つかりません"; \
			exit 1; \
		fi \
	done
	@for dir in words kanjis; do \
		for subdir in endpoints; do \
			if [ ! -d "app/api/v1/$$dir/$$subdir" ]; then \
				echo "Error: app/api/v1/$$dir/$$subdirディレクトリが見つかりません"; \
				exit 1; \
			fi \
		done; \
		for file in app.py endpoints/__init__.py requirements.txt requirements-dev.txt; do \
			if [ ! -f "app/api/v1/$$dir/$$file" ]; then \
				echo "Error: app/api/v1/$$dir/$$fileが見つかりません"; \
				exit 1; \
			fi \
		done \
	done

# クリーンアップ
clean: clean-common
	@echo "クリーンアップを実行中..."
	@rm -rf .aws-sam

# バックアップ作成
backup:
	@echo "バックアップを作成しています..."
	@if [ -d "app/api/v1/words/common" ]; then \
		mv app/api/v1/words/common app/api/v1/words/common_backup_$$(date +%Y%m%d_%H%M%S); \
	fi
	@if [ -d "app/api/v1/kanjis/common" ]; then \
		mv app/api/v1/kanjis/common app/api/v1/kanjis/common_backup_$$(date +%Y%m%d_%H%M%S); \
	fi

# SAMビルド
build:
	@echo "SAMでビルドを実行中..."
	@sam build

# ロールバック
rollback:
	@echo "ロールバックを実行します..."
	@if ls app/api/v1/words/common_backup_* 1> /dev/null 2>&1; then \
		latest_backup=$$(ls -td app/api/v1/words/common_backup_* | head -1); \
		rm -rf app/api/v1/words/common; \
		mv $$latest_backup app/api/v1/words/common; \
	fi
	@if ls app/api/v1/kanjis/common_backup_* 1> /dev/null 2>&1; then \
		latest_backup=$$(ls -td app/api/v1/kanjis/common_backup_* | head -1); \
		rm -rf app/api/v1/kanjis/common; \
		mv $$latest_backup app/api/v1/kanjis/common; \
	fi
	aws cloudformation delete-stack --stack-name japanese-learn

# デプロイ後の確認
verify:
	@echo "デプロイの確認を行います..."
	@echo "Words Functionのデプロイを確認中..."
	@aws lambda get-function --function-name japanese-learn-WordsFunction > /dev/null
	@echo "Kanjis Functionのデプロイを確認中..."
	@aws lambda get-function --function-name japanese-learn-KanjisFunction > /dev/null
	@echo "デプロイの確認が完了しました"

# AWS認証情報の設定
setup-aws:
	@echo "AWS認証情報を設定しています..."
	@aws configure set aws_access_key_id "$$CUSTOM_AWS_ACCESS_KEY"
	@aws configure set aws_secret_access_key "$$CUSTOM_AWS_SECRET_KEY"
	@aws configure set region "$$CUSTOM_AWS_REGION"
	@echo "AWS認証情報の設定を確認しています..."
	@aws sts get-caller-identity >/dev/null 2>&1 || { echo "Error: AWS認証情報の設定に失敗しました"; exit 1; }

# ヘルプ
help:
	@echo "利用可能なコマンド:"
	@echo "  make deploy        - デプロイを実行"
	@echo "  make dev-setup    - 開発環境のセットアップ手順を表示"
	@echo "  make check-env    - AWS環境とデータベース環境変数の確認"
	@echo "  make check-deps   - 依存関係の確認"
	@echo "  make check-structure - ファイル構造の確認"
	@echo "  make clean        - .aws-samを削除"
	@echo "  make build        - SAMでビルドを実行"
	@echo "  make verify       - デプロイ後の確認を実行"
	@echo "  make setup-aws    - AWS認証情報を設定"
	@echo "  make help         - このヘルプを表示"

prepare-build:
	@echo "共通コードをコピーしています..."
	@for dir in words kanjis learn_words; do \
		echo "$$dirにcommonをコピー中..."; \
		cp -r "app/api/v1/common" "app/api/v1/$$dir/"; \
	done

clean-common:
	@echo "共通コードをクリーンアップしています..."
	@for dir in words kanjis learn_words; do \
		echo "Removing app/api/v1/$$dir/common..."; \
		if [ -d "app/api/v1/$$dir/common" ]; then \
			rm -rf "app/api/v1/$$dir/common" && echo "Successfully removed $$dir/common" || echo "Failed to remove $$dir/common"; \
		else \
			echo "Directory $$dir/common does not exist"; \
		fi; \
	done 