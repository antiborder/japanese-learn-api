#!/bin/bash
# Get /api/v1 resource ID from API Gateway

REST_API_ID="${1:-omqihdsdi1}"
REGION="${2:-ap-northeast-1}"

RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id ${REST_API_ID} \
  --region ${REGION} \
  --query "items[?path=='/api/v1'].Id" \
  --output text)

echo "Resource ID for /api/v1: ${RESOURCE_ID}"

