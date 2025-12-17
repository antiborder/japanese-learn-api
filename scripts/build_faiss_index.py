#!/usr/bin/env python3
"""
Script to build FAISS index from DynamoDB embeddings and save to S3
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Load environment variables from .env file
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if os.path.exists(env_file):
    logger.info(f"Loaded environment variables from {env_file}")
else:
    logger.warning(f".env file not found at {env_file}")

# Add chat module path for relative imports
chat_module_path = os.path.join(project_root, 'app', 'api', 'v1', 'chat')
sys.path.insert(0, chat_module_path)

# Change to chat module directory for relative imports to work
original_cwd = os.getcwd()
os.chdir(chat_module_path)

try:
    from integrations.vector_store import FAISSVectorStore
finally:
    os.chdir(original_cwd)

def main():
    logger.info("Building FAISS index...")
    logger.info(f"FAISS_INDEX_S3_BUCKET_NAME: {os.getenv('FAISS_INDEX_S3_BUCKET_NAME', 'NOT SET')}")
    logger.info(f"DYNAMODB_TABLE_NAME: {os.getenv('DYNAMODB_TABLE_NAME', 'NOT SET')}")
    
    vector_store = FAISSVectorStore()
    
    # Build index from DynamoDB
    vector_store.build_index_from_dynamodb()
    
    # Save to S3
    try:
        vector_store.save_to_s3()
        logger.info("FAISS index built and saved successfully")
    except Exception as e:
        logger.error(f"Failed to save index to S3: {e}")
        logger.info("Index built but not saved to S3. You may need to configure S3 permissions.")
        sys.exit(1)

if __name__ == '__main__':
    main()

