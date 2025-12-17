#!/bin/bash
# ECRリポジトリを作成するスクリプト

set -e

# 設定
AWS_REGION="${AWS_REGION:-ap-northeast-1}"
STACK_NAME="${STACK_NAME:-japanese-learn}"
ECR_REPO="${STACK_NAME}-chat-function"

echo "Creating ECR repository: ${ECR_REPO}"

# ECRリポジトリを作成
aws ecr create-repository \
    --repository-name ${ECR_REPO} \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true \
    --image-tag-mutability MUTABLE

echo "✅ ECR repository created: ${ECR_REPO}"

