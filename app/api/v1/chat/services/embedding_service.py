"""
Embedding service for generating vector embeddings using AWS Bedrock Titan
"""
import boto3
import json
import os
import logging
from typing import List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'ap-northeast-1'))
        self.model_id = 'amazon.titan-embed-text-v1'
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table'))
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using Bedrock Titan
        
        Args:
            text: Text to embed
            
        Returns:
            List of 1536 float values (embedding vector)
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return [0.0] * 1536
            
            # Call Bedrock API
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'inputText': text
                })
            )
            
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding', [])
            
            if len(embedding) != 1536:
                logger.warning(f"Unexpected embedding dimension: {len(embedding)}, expected 1536")
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Bedrock Titan doesn't support batch API, so we call sequentially
            # But we can optimize by filtering empty texts
            embeddings = []
            for text in texts:
                if text and text.strip():
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                else:
                    # Return zero vector for empty text
                    embeddings.append([0.0] * 1536)
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def get_text_for_embedding(self, item: dict, entity_type: str) -> str:
        """
        Extract text to embed from DynamoDB item
        
        Args:
            item: DynamoDB item
            entity_type: 'word', 'kanji', or 'sentence'
            
        Returns:
            Text string to embed
        """
        if entity_type == 'word':
            # Combine japanese, english, and other language fields
            parts = []
            if item.get('name'):
                parts.append(item['name'])
            if item.get('hiragana'):
                parts.append(item['hiragana'])
            if item.get('english'):
                parts.append(item['english'])
            # Add other languages if available
            for lang in ['vietnamese', 'chinese', 'korean']:
                if item.get(lang):
                    parts.append(item[lang])
            return ' '.join(parts)
        
        elif entity_type == 'kanji':
            parts = []
            # Try both 'kanji' and 'character' field names for compatibility
            kanji_char = item.get('kanji') or item.get('character', '')
            if kanji_char:
                parts.append(kanji_char)
            if item.get('meaning'):
                parts.append(item['meaning'])
            if item.get('reading'):
                parts.append(item['reading'])
            return ' '.join(parts)
        
        elif entity_type == 'sentence':
            parts = []
            if item.get('japanese'):
                parts.append(item['japanese'])
            if item.get('english'):
                parts.append(item['english'])
            return ' '.join(parts)
        
        return ""
    
    def store_embedding(self, pk: str, sk: str, embedding: List[float]):
        """
        Store embedding in DynamoDB item
        
        Args:
            pk: Partition key
            sk: Sort key
            embedding: Embedding vector (list of floats)
        """
        try:
            # Convert float list to Decimal list for DynamoDB compatibility
            embedding_decimal = [Decimal(str(float_val)) for float_val in embedding]
            
            self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression='SET embedding = :embedding',
                ExpressionAttributeValues={
                    ':embedding': embedding_decimal
                }
            )
            logger.info(f"Stored embedding for {pk}/{sk}")
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            raise

