#!/bin/bash
# ChatTestFunction Lambda関数のDockerイメージをビルドしてECRにプッシュするスクリプト

set -e

# 設定
AWS_REGION="${AWS_REGION:-ap-northeast-1}"
STACK_NAME="${STACK_NAME:-japanese-learn}"
ECR_REPO="${STACK_NAME}-chat-function"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# AWSアカウントIDを取得
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo "Building Docker image for ChatTestFunction..."
echo "ECR Repository: ${ECR_URI}"
echo "Image Tag: ${IMAGE_TAG}"

# ECRリポジトリが存在するか確認、存在しなければ作成を試みる
echo "Checking if ECR repository exists..."
if ! aws ecr describe-repositories --repository-names ${ECR_REPO} --region ${AWS_REGION} > /dev/null 2>&1; then
    echo "⚠️  ECR repository does not exist."
    echo "Please create it manually via AWS Console or CLI:"
    echo ""
    echo "aws ecr create-repository \\"
    echo "  --repository-name ${ECR_REPO} \\"
    echo "  --region ${AWS_REGION} \\"
    echo "  --image-scanning-configuration scanOnPush=true \\"
    echo "  --image-tag-mutability MUTABLE"
    echo ""
    echo "Or create it via AWS Console:"
    echo "1. Go to ECR in AWS Console"
    echo "2. Click 'Create repository'"
    echo "3. Repository name: ${ECR_REPO}"
    echo "4. Enable 'Scan on push'"
    echo "5. Click 'Create repository'"
    exit 1
else
    echo "✅ ECR repository exists: ${ECR_REPO}"
fi

# 作業ディレクトリに移動
cd "$(dirname "$0")/../app/api/v1/chat-test"

# Dockerイメージをビルド（Lambdaはx86_64アーキテクチャをサポート）
echo "Building Docker image for x86_64 (Lambda compatible)..."
docker buildx build --platform linux/amd64 -t ${ECR_REPO}:${IMAGE_TAG} --load .

# ECRにログイン
echo "Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# イメージにタグを付ける
echo "Tagging image..."
docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}

# ECRにプッシュ
echo "Pushing image to ECR..."
docker push ${ECR_URI}:${IMAGE_TAG}

echo "✅ Successfully pushed ${ECR_URI}:${IMAGE_TAG}"
echo ""
echo "Next steps:"
echo "1. Run 'sam deploy' to update the Lambda function"
echo "2. Or update the Lambda function manually:"
echo "   aws lambda update-function-code --function-name ${STACK_NAME}-ChatTestFunction --image-uri ${ECR_URI}:${IMAGE_TAG} --region ${AWS_REGION}"

