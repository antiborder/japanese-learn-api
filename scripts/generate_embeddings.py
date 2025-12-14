#!/usr/bin/env python3
"""
Script to generate embeddings for DynamoDB items (words, kanjis, sentences)
"""
import boto3
import os
import sys
import argparse
import logging
from tqdm import tqdm
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.api.v1.chat.services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_embeddings_for_entity_type(
    embedding_service: EmbeddingService,
    entity_type: str,
    limit: Optional[int] = None
):
    """
    Generate embeddings for all items of a given entity type
    
    Args:
        embedding_service: EmbeddingService instance
        entity_type: 'word', 'kanji', or 'sentence'
        limit: Optional limit for testing
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table')
    table = dynamodb.Table(table_name)
    
    # Map entity types to PK values
    pk_map = {
        'word': 'WORD',
        'kanji': 'KANJI',
        'sentence': 'SENTENCE'
    }
    
    pk = pk_map.get(entity_type)
    if not pk:
        raise ValueError(f"Unknown entity type: {entity_type}")
    
    # Query all items
    logger.info(f"Querying {entity_type} items...")
    items = []
    last_evaluated_key = None
    
    while True:
        query_params = {
            'KeyConditionExpression': 'PK = :pk',
            'ExpressionAttributeValues': {':pk': pk}
        }
        if last_evaluated_key:
            query_params['ExclusiveStartKey'] = last_evaluated_key
        
        response = table.query(**query_params)
        items.extend(response.get('Items', []))
        
        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break
        
        if limit and len(items) >= limit:
            items = items[:limit]
            break
    
    logger.info(f"Found {len(items)} {entity_type} items")
    
    # Filter items without embeddings
    items_to_process = [
        item for item in items 
        if 'embedding' not in item or not item.get('embedding')
    ]
    
    logger.info(f"Processing {len(items_to_process)} items without embeddings")
    
    if not items_to_process:
        logger.info("All items already have embeddings")
        return
    
    # Process items
    failed = 0
    success = 0
    
    for item in tqdm(items_to_process, desc=f"Processing {entity_type}"):
        try:
            # Extract text to embed
            text = embedding_service.get_text_for_embedding(item, entity_type)
            
            if not text or not text.strip():
                logger.warning(f"Skipping {entity_type} {item.get('SK')} - no text to embed")
                continue
            
            # Generate embedding
            embedding = embedding_service.generate_embedding(text)
            
            # Store embedding
            embedding_service.store_embedding(
                item['PK'],
                item['SK'],
                embedding
            )
            success += 1
            
        except Exception as e:
            logger.error(f"Failed to process {entity_type} {item.get('SK')}: {e}")
            failed += 1
    
    logger.info(f"Completed {entity_type}. Success: {success}, Failed: {failed}")

def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for DynamoDB items')
    parser.add_argument('--entity-type', choices=['word', 'kanji', 'sentence', 'all'],
                       default='all', help='Entity type to process')
    parser.add_argument('--limit', type=int, help='Limit number of items (for testing)')
    parser.add_argument('--aws-region', default='ap-northeast-1', help='AWS region')
    
    args = parser.parse_args()
    
    # Set AWS region
    os.environ['AWS_REGION'] = args.aws_region
    
    embedding_service = EmbeddingService()
    
    if args.entity_type == 'all':
        for entity_type in ['word', 'kanji', 'sentence']:
            logger.info(f"\n=== Processing {entity_type} ===")
            generate_embeddings_for_entity_type(embedding_service, entity_type, args.limit)
    else:
        generate_embeddings_for_entity_type(embedding_service, args.entity_type, args.limit)

if __name__ == '__main__':
    main()

