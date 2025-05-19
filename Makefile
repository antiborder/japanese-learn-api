.PHONY: deploy clean build package upload cleanup

deploy: clean build package upload cleanup

clean:
	docker start my_lambda_env
	docker exec my_lambda_env mkdir -p /python
	docker exec my_lambda_env rm -rf /python/*

build:
	docker cp app my_lambda_env:/python/
	docker cp requirements.txt my_lambda_env:/python/
	docker cp google-tts-key.json my_lambda_env:/python/
	docker exec my_lambda_env bash -c "cd /python && mkdir -p packages && \
		pip3 install --no-cache-dir --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: --upgrade -r requirements.txt --target ./packages && \
		pip3 install --no-cache-dir grpcio grpcio-status google-cloud-texttospeech --target ./packages"

package:
	docker exec my_lambda_env bash -c "cd /python && cp -r app packages/ && \
		cp google-tts-key.json packages/ && \
		cd packages && \
		find . -name '*aarch64*.so' -delete && \
		find . -name '*.pyx' -delete && \
		find . -name '*.pxd' -delete && \
		find . -name '*.h' -delete && \
		find . -name '*.c' -delete && \
		find . -name '*.pyc' -delete && \
		find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && \
		zip -r /lambda.zip *"
	docker cp my_lambda_env:/lambda.zip .

upload:
	aws s3 cp lambda.zip s3://bucket-japanese-learn/lambda.zip
	aws lambda update-function-code --function-name japanese-learn-stack-JapaneseLearnFunction-Mgf0XxGrAW6M --s3-bucket bucket-japanese-learn --s3-key lambda.zip

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