include .env
export

.PHONY: deploy clean build build-chat-container check-env check-aws-env check-db-env check-deps check-structure backup verify help rollback setup-aws dev-setup prepare-build clean-common

# デフォルトターゲット
.DEFAULT_GOAL := help

# シェルの設定
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# デプロイ（全ステップを実行）
deploy: check-env check-deps check-structure prepare-build build-chat-container build setup-aws
	@echo "デプロイを実行します..."
	@echo "SAMのバージョンを確認しています..."
	@sam --version
	@echo "デプロイ開始..."
	@AWS_ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	AWS_REGION=$${CUSTOM_AWS_REGION:-ap-northeast-1}; \
	API_V1_RESOURCE_ID="w4iw1z"; \
	API_ID=$$(aws cloudformation describe-stacks --stack-name japanese-learn --query "Stacks[0].Outputs[?OutputKey=='ApiId'].OutputValue" --output text --region $$AWS_REGION 2>/dev/null || echo ""); \
	if [ -n "$$API_ID" ]; then \
		RESOURCE_ID=$$(aws apigateway get-resources --rest-api-id $$API_ID --region $$AWS_REGION --query "items[?path=='/api/v1'].Id" --output text 2>/dev/null || echo ""); \
		if [ -n "$$RESOURCE_ID" ]; then \
			API_V1_RESOURCE_ID="$$RESOURCE_ID"; \
		fi; \
	fi; \
	echo "Using ApiV1ResourceId: $$API_V1_RESOURCE_ID"; \
	sam deploy \
		--stack-name japanese-learn \
		--resolve-s3 \
		--image-repository $$AWS_ACCOUNT_ID.dkr.ecr.$$AWS_REGION.amazonaws.com/japanese-learn-chat-function \
		--parameter-overrides \
		S3BucketName="$$S3_BUCKET_NAME" \
		GoogleApiKey="$$GOOGLE_API_KEY" \
		GoogleSearchEngineId="$$GOOGLE_SEARCH_ENGINE_ID" \
		GeminiApiKey="$$GEMINI_API_KEY" \
		FrontendBaseUrl="$$FRONTEND_BASE_URL" \
		ApiV1ResourceId="$$API_V1_RESOURCE_ID" \
		--capabilities CAPABILITY_IAM \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset \
		--no-progressbar \
		|| { echo "デプロイに失敗しました。"; exit 1; }
	@echo "ChatFunctionのLambda関数を更新しています..."
	@CHAT_FUNCTION_NAME=$$(aws lambda list-functions --region $$AWS_REGION --query "Functions[?contains(FunctionName, 'ChatFunction') && !contains(FunctionName, 'ChatTest')].FunctionName" --output text | head -1); \
	if [ -n "$$CHAT_FUNCTION_NAME" ]; then \
		echo "Found ChatFunction: $$CHAT_FUNCTION_NAME"; \
		echo "Updating Lambda function to latest ECR image..."; \
		UPDATE_RESULT=$$(aws lambda update-function-code \
			--function-name "$$CHAT_FUNCTION_NAME" \
			--image-uri "$$AWS_ACCOUNT_ID.dkr.ecr.$$AWS_REGION.amazonaws.com/japanese-learn-chat-function:latest" \
			--region $$AWS_REGION \
			--query '{FunctionName:FunctionName, LastModified:LastModified, CodeSha256:CodeSha256, State:State, LastUpdateStatus:LastUpdateStatus}' \
			--output json 2>&1); \
		if [ $$? -eq 0 ]; then \
			echo "✅ Lambda function update initiated:"; \
			echo "$$UPDATE_RESULT" | python3 -m json.tool 2>/dev/null || echo "$$UPDATE_RESULT"; \
		else \
			echo "⚠️  Warning: Failed to update Lambda function:"; \
			echo "$$UPDATE_RESULT"; \
		fi; \
	else \
		echo "⚠️  Warning: ChatFunction not found in Lambda functions list"; \
	fi
	@echo "API Gatewayリソースを確認しています..."
	@API_ID=$$(aws cloudformation describe-stacks --stack-name japanese-learn --query "Stacks[0].Outputs[?OutputKey=='ApiId'].OutputValue" --output text --region $$AWS_REGION 2>/dev/null || echo ""); \
	if [ -n "$$API_ID" ]; then \
		echo "Checking API Gateway resources for /api/v1/chat..."; \
		CHAT_RESOURCES=$$(aws apigateway get-resources --rest-api-id $$API_ID --region $$AWS_REGION --query "items[?contains(path, '/chat')]" --output json 2>/dev/null || echo "[]"); \
		CHAT_COUNT=$$(echo "$$CHAT_RESOURCES" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0"); \
		if [ "$$CHAT_COUNT" -eq "0" ]; then \
			echo "⚠️  Warning: /api/v1/chat resources not found in API Gateway"; \
		else \
			echo "✅ Found $$CHAT_COUNT chat resource(s) in API Gateway"; \
		fi; \
		echo "Creating/updating API Gateway deployment for Prod stage..."; \
		DEPLOYMENT_ID=$$(aws apigateway create-deployment \
			--rest-api-id $$API_ID \
			--stage-name Prod \
			--region $$AWS_REGION \
			--description "Deploy ChatFunction resources - $$(date +%Y-%m-%d\ %H:%M:%S)" \
			--output text \
			--query 'id' 2>/dev/null || echo ""); \
		if [ -n "$$DEPLOYMENT_ID" ]; then \
			echo "✅ API Gateway deployment created/updated: $$DEPLOYMENT_ID"; \
		else \
			echo "⚠️  Warning: Failed to create deployment (may already exist or need manual deployment)"; \
		fi; \
	else \
		echo "⚠️  Warning: API ID not found"; \
	fi
	@echo "デプロイが完了しました"
	@make verify
	@make clean-common
	@make clean

# Chat LambdaコンテナのDockerイメージをビルドしてECRにプッシュ
build-chat-container:
	@echo "Chat LambdaコンテナのDockerイメージをビルドしてECRにプッシュします..."
	@./scripts/build_and_push_chat_function.sh

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
	@test -n "$$S3_BUCKET_NAME" || { echo "Error: S3_BUCKET_NAMEが設定されていません"; exit 1; }
	@test -n "$$GOOGLE_API_KEY" || { echo "Error: GOOGLE_API_KEYが設定されていません"; exit 1; }
	@test -n "$$GOOGLE_SEARCH_ENGINE_ID" || { echo "Error: GOOGLE_SEARCH_ENGINE_IDが設定されていません"; exit 1; }
	@test -n "$$GEMINI_API_KEY" || { echo "Error: GEMINI_API_KEYが設定されていません"; exit 1; }

# 依存関係チェック
check-deps:
	@echo "依存関係を確認しています..."
	@for dir in app/api/v1/words app/api/v1/kanjis app/api/v1/learn_words app/api/v1/search app/api/v1/sentences app/api/v1/users app/api/v1/hiragana app/api/v1/kana_lesson app/api/v1/chat app/api/v1/admin; do \
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
	@for file in config.py; do \
		if [ ! -f "app/api/v1/common/$$file" ]; then \
			echo "Error: app/api/v1/common/$$fileが見つかりません"; \
			exit 1; \
		fi \
	done
	@for dir in words kanjis learn_words search sentences users hiragana kana_lesson chat; do \
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
	@echo "Users Functionのデプロイを確認中..."
	@aws lambda get-function --function-name japanese-learn-UsersFunction > /dev/null
	@echo "Kana Lesson Functionのデプロイを確認中..."
	@aws lambda get-function --function-name japanese-learn-KanaLessonFunction > /dev/null
	@echo "Chat Functionのデプロイを確認中..."
	@CHAT_FUNCTION_NAME=$$(aws lambda list-functions --region ap-northeast-1 --query "Functions[?contains(FunctionName, 'ChatFunction') && !contains(FunctionName, 'ChatTest')].FunctionName" --output text | head -1); \
	if [ -n "$$CHAT_FUNCTION_NAME" ]; then \
		aws lambda get-function --function-name "$$CHAT_FUNCTION_NAME" > /dev/null && echo "Chat Function found: $$CHAT_FUNCTION_NAME"; \
	else \
		echo "Warning: Chat Function not found"; \
	fi
	@echo "Admin Functionのデプロイを確認中..."
	@aws lambda get-function --function-name japanese-learn-AdminFunction > /dev/null
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
	@echo "  make deploy              - デプロイを実行（chatコンテナ含む）"
	@echo "  make build-chat-container - Chat LambdaコンテナのDockerイメージをビルドしてECRにプッシュ"
	@echo "  make dev-setup           - 開発環境のセットアップ手順を表示"
	@echo "  make check-env           - AWS環境とデータベース環境変数の確認"
	@echo "  make check-deps          - 依存関係の確認"
	@echo "  make check-structure     - ファイル構造の確認"
	@echo "  make clean               - .aws-samを削除"
	@echo "  make build               - SAMでビルドを実行"
	@echo "  make verify              - デプロイ後の確認を実行"
	@echo "  make setup-aws           - AWS認証情報を設定"
	@echo "  make help                - このヘルプを表示"

prepare-build:
	@echo "共通コードをコピーしています..."
	@for dir in words kanjis learn_words search sentences users hiragana kana_lesson chat admin; do \
		echo "$$dirにcommonをコピー中..."; \
		cp -r "app/api/v1/common" "app/api/v1/$$dir/"; \
	done

clean-common:
	@echo "共通コードをクリーンアップしています..."
	@for dir in words kanjis learn_words search sentences users hiragana kana_lesson chat admin; do \
		echo "Removing app/api/v1/$$dir/common..."; \
		if [ -d "app/api/v1/$$dir/common" ]; then \
			rm -rf "app/api/v1/$$dir/common" && echo "Successfully removed $$dir/common" || echo "Failed to remove $$dir/common"; \
		else \
			echo "Directory $$dir/common does not exist"; \
		fi; \
	done 