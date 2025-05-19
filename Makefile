.PHONY: deploy clean build package upload cleanup

deploy: clean build package upload cleanup

clean:
	docker start my_lambda_env
	docker exec my_lambda_env mkdir -p /python
	docker exec my_lambda_env rm -rf /python/*

build:
	docker cp app my_lambda_env:/python/
	docker cp requirements.txt my_lambda_env:/python/
	docker exec my_lambda_env bash -c "cd /python && mkdir -p packages && pip3 install -r requirements.txt --target ./packages"

package:
	docker exec my_lambda_env bash -c "cd /python && cp -r app packages/ && cd packages && zip -r /lambda.zip *"
	docker cp my_lambda_env:/lambda.zip .

upload:
	aws lambda update-function-code --function-name japanese-learn-stack-JapaneseLearnFunction-Mgf0XxGrAW6M --zip-file fileb://lambda.zip

cleanup:
	rm -f lambda.zip
	docker exec my_lambda_env rm -rf /python/packages

help:
	@echo "使用可能なコマンド:"
	@echo "  make deploy  - クリーン、ビルド、パッケージング、アップロード、クリーンアップを実行"
	@echo "  make clean   - Pythonディレクトリをクリーンアップ"
	@echo "  make build   - アプリケーションをビルド"
	@echo "  make package - Lambda用にパッケージング"
	@echo "  make upload  - AWSにアップロード"
	@echo "  make cleanup - 一時ファイルを削除" 