.PHONY: deploy clean build package upload

deploy: clean build package upload

clean:
	docker start my_lambda_env
	docker exec my_lambda_env mkdir -p /python
	docker exec my_lambda_env rm -rf /python/*

build:
	docker cp app my_lambda_env:/python/
	docker cp requirements.txt my_lambda_env:/python/
	docker exec my_lambda_env bash -c "cd /python && pip3 install -r requirements.txt -t ."

package:
	docker exec my_lambda_env bash -c "cd /python && zip -r /lambda.zip *"
	docker cp my_lambda_env:/lambda.zip .

upload:
	aws lambda update-function-code --function-name japanese-learn-lambdaJapaneseLearn-UzpN0784du5X --zip-file fileb://lambda.zip

help:
	@echo "使用可能なコマンド:"
	@echo "  make deploy  - クリーン、ビルド、パッケージング、アップロードを実行"
	@echo "  make clean   - Pythonディレクトリをクリーンアップ"
	@echo "  make build   - アプリケーションをビルド"
	@echo "  make package - Lambda用にパッケージング"
	@echo "  make upload  - AWSにアップロード" 