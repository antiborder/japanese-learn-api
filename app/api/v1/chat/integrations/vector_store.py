"""
Vector store service using FAISS for semantic search
"""
import faiss
import pickle
import boto3
import os
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple

# Try relative import first, fallback to absolute import
try:
    from services.embedding_service import EmbeddingService
except ImportError:
    from app.api.v1.chat.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.index: Optional[faiss.Index] = None
        self.id_mapping: Dict[int, Dict] = {}  # FAISS index -> (PK, SK, entity_type, item_data)
        self.s3_client = boto3.client('s3')
        self.s3_bucket = os.getenv('FAISS_INDEX_S3_BUCKET_NAME')
        self.index_key = os.getenv('FAISS_INDEX_S3_KEY', 'faiss_index/index.faiss')
        self.metadata_key = os.getenv('FAISS_INDEX_METADATA_S3_KEY', 'faiss_index/metadata.pkl')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table'))
    
    def build_index_from_dynamodb(self):
        """
        Build FAISS index from DynamoDB embeddings
        """
        import time
        start_time = time.time()
        logger.info("Building FAISS index from DynamoDB...")
        
        # Collect all items with embeddings
        embeddings_list = []
        id_mapping = {}
        
        entity_types = ['WORD', 'KANJI', 'SENTENCE']
        
        for pk in entity_types:
            last_evaluated_key = None
            while True:
                query_params = {
                    'KeyConditionExpression': 'PK = :pk',
                    'FilterExpression': 'attribute_exists(embedding)',
                    'ExpressionAttributeValues': {':pk': pk}
                }
                if last_evaluated_key:
                    query_params['ExclusiveStartKey'] = last_evaluated_key
                
                response = self.table.query(**query_params)
                items = response.get('Items', [])
                
                for item in items:
                    embedding = item.get('embedding')
                    if embedding and isinstance(embedding, list) and len(embedding) == 1536:
                        embeddings_list.append(embedding)
                        
                        idx = len(embeddings_list) - 1
                        # Store only essential fields to reduce memory usage
                        # Full item data is not needed - we can fetch from DynamoDB if needed
                        mapping_data = {
                            'pk': item['PK'],
                            'sk': item['SK'],
                            'entity_type': pk.lower()
                        }
                        
                        # Store only essential fields based on entity type to reduce memory
                        if pk == 'WORD':
                            mapping_data.update({
                                'name': item.get('name', ''),
                                'hiragana': item.get('hiragana', ''),
                                'english': item.get('english', ''),
                                'level': item.get('level', 0)
                            })
                        elif pk == 'KANJI':
                            mapping_data.update({
                                'kanji': item.get('kanji') or item.get('character', ''),
                                'meaning': item.get('meaning', ''),
                                'reading': item.get('reading', '')
                            })
                        elif pk == 'SENTENCE':
                            mapping_data.update({
                                'japanese': item.get('japanese', ''),
                                'english': item.get('english', '')
                            })
                        
                        id_mapping[idx] = mapping_data
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
        
        logger.info(f"Found {len(embeddings_list)} items with embeddings")
        
        if not embeddings_list:
            logger.warning("No items with embeddings found")
            # Create empty index
            dimension = 1536
            self.index = faiss.IndexFlatL2(dimension)
            self.id_mapping = {}
            return
        
        # Build FAISS index
        embeddings_array = np.array(embeddings_list, dtype=np.float32)
        
        # Create FAISS index (L2 distance)
        dimension = 1536
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        
        self.id_mapping = id_mapping
        
        total_time = time.time() - start_time
        logger.info(f"Built FAISS index with {self.index.ntotal} vectors (total time: {total_time:.2f} seconds)")
    
    def save_to_s3(self):
        """Save FAISS index and metadata to S3"""
        if not self.index:
            raise ValueError("No index to save")
        
        # Check if S3 bucket is configured
        if not self.s3_bucket:
            raise ValueError("FAISS_INDEX_S3_BUCKET_NAME not set. Cannot save index to S3.")
        
        logger.info(f"Saving FAISS index to S3 bucket: {self.s3_bucket}")
        
        # Create temporary directory
        os.makedirs('/tmp/faiss_index', exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, '/tmp/faiss_index/index.faiss')
        
        # Save metadata
        metadata = {
            'id_mapping': self.id_mapping,
            'total_vectors': self.index.ntotal
        }
        
        with open('/tmp/faiss_index/metadata.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        # Upload to S3
        try:
            self.s3_client.upload_file(
                '/tmp/faiss_index/index.faiss',
                self.s3_bucket,
                self.index_key
            )
            
            self.s3_client.upload_file(
                '/tmp/faiss_index/metadata.pkl',
                self.s3_bucket,
                self.metadata_key
            )
            
            logger.info("FAISS index saved to S3")
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise
    
    def load_from_s3(self) -> bool:
        """Load FAISS index from S3"""
        import time
        start_time = time.time()
        
        try:
            # Check if S3 bucket is configured
            if not self.s3_bucket:
                logger.warning("FAISS_INDEX_S3_BUCKET_NAME not set, skipping S3 load")
                return False
            
            logger.info(f"Loading FAISS index from S3 (bucket: {self.s3_bucket}, key: {self.index_key})...")
            
            # Create temporary directory
            os.makedirs('/tmp/faiss_index', exist_ok=True)
            
            # Download from S3 with timeout
            from botocore.config import Config
            config = Config(
                read_timeout=30,  # 30秒でタイムアウト（インデックスファイルが大きい場合）
                connect_timeout=10
            )
            s3_client = boto3.client('s3', config=config)
            
            # Check if file exists first
            try:
                logger.info("Checking if index file exists in S3...")
                s3_client.head_object(Bucket=self.s3_bucket, Key=self.index_key)
                logger.info("Index file found in S3")
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logger.warning(f"FAISS index not found in S3: {self.index_key}")
                    return False
                logger.error(f"Error checking S3 file: {e}")
                raise
            
            # Download from S3
            logger.info("Downloading index file from S3...")
            download_start = time.time()
            s3_client.download_file(
                self.s3_bucket,
                self.index_key,
                '/tmp/faiss_index/index.faiss'
            )
            logger.info(f"Index file downloaded in {time.time() - download_start:.2f} seconds")
            
            logger.info("Downloading metadata file from S3...")
            s3_client.download_file(
                self.s3_bucket,
                self.metadata_key,
                '/tmp/faiss_index/metadata.pkl'
            )
            
            # Load FAISS index
            logger.info("Loading FAISS index into memory...")
            load_start = time.time()
            self.index = faiss.read_index('/tmp/faiss_index/index.faiss')
            logger.info(f"FAISS index loaded in {time.time() - load_start:.2f} seconds")
            
            # Load metadata
            with open('/tmp/faiss_index/metadata.pkl', 'rb') as f:
                metadata = pickle.load(f)
                self.id_mapping = metadata.get('id_mapping', {})
            
            total_time = time.time() - start_time
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors (total time: {total_time:.2f} seconds)")
            return True
        
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error loading FAISS index from S3 (elapsed: {elapsed:.2f}s): {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def similarity_search(self, query: str, k: int = 5, entity_type: Optional[str] = None) -> List[Dict]:
        """
        Search for similar items using vector similarity
        
        Args:
            query: Search query text
            k: Number of results to return
            entity_type: Optional filter by entity type ('word', 'kanji', 'sentence')
            
        Returns:
            List of similar items with scores
        """
        if not self.index or self.index.ntotal == 0:
            logger.warning("Index not loaded or empty, building from DynamoDB...")
            self.build_index_from_dynamodb()
            if not self.index or self.index.ntotal == 0:
                logger.warning("No index available, returning empty results")
                return []
        
        try:
            logger.info(f"Generating embedding for query: '{query}'")
            # Generate embedding for query
            query_embedding = self.embedding_service.generate_embedding(query)
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Search - get more results to filter by entity type
            search_k = k * 10 if entity_type else k  # Get more results if filtering by entity type
            search_k = min(search_k, self.index.ntotal)
            logger.info(f"Searching FAISS index with k={search_k}")
            distances, indices = self.index.search(query_vector, search_k)
            
            # Convert results to item format
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS returns -1 for invalid indices
                    continue
                
                mapping = self.id_mapping.get(int(idx))
                if not mapping:
                    continue
                
                # Filter by entity type if specified
                if entity_type and mapping.get('entity_type') != entity_type:
                    continue
                
                # Helper function to convert DynamoDB types to Python native types
                def convert_dynamodb_value(value):
                    """Convert DynamoDB types (Decimal, etc.) to Python native types"""
                    from decimal import Decimal
                    if isinstance(value, Decimal):
                        # Convert Decimal to int if it's a whole number, otherwise float
                        if value % 1 == 0:
                            return int(value)
                        return float(value)
                    elif isinstance(value, dict):
                        return {k: convert_dynamodb_value(v) for k, v in value.items()}
                    elif isinstance(value, list):
                        return [convert_dynamodb_value(v) for v in value]
                    return value
                
                # Extract relevant fields based on entity type
                entity_type_from_mapping = mapping.get('entity_type', '')
                word_id = int(mapping.get('sk', 0))
                
                result = {
                    'id': word_id,
                    'score': float(distance),
                    'entity_type': entity_type_from_mapping
                }
                
                if entity_type_from_mapping == 'word':
                    # Check if we have the required fields in mapping
                    name = mapping.get('name', '')
                    hiragana = mapping.get('hiragana', '')
                    english = mapping.get('english', '')
                    level = mapping.get('level', 0)
                    
                    # If fields are missing, fetch from DynamoDB as fallback
                    if not name or not hiragana or not english:
                        logger.warning(f"Missing fields in id_mapping for word_id {word_id}, fetching from DynamoDB...")
                        try:
                            response = self.table.get_item(
                                Key={
                                    'PK': 'WORD',
                                    'SK': str(word_id)
                                }
                            )
                            item = response.get('Item')
                            if item:
                                name = item.get('name', '')
                                hiragana = item.get('hiragana', '')
                                english = item.get('english', '')
                                level = item.get('level', 0)
                                logger.info(f"Fetched from DynamoDB: name={name}, hiragana={hiragana}, english={english}")
                        except Exception as e:
                            logger.error(f"Error fetching word {word_id} from DynamoDB: {e}")
                    
                    # Convert DynamoDB values to native Python types
                    if level is not None:
                        level = convert_dynamodb_value(level)
                        # Ensure level is a number
                        if isinstance(level, (int, float)):
                            level = int(level)
                        else:
                            level = 0
                    else:
                        level = 0
                    
                    result.update({
                        'name': str(name),
                        'hiragana': str(hiragana),
                        'english': str(english),
                        'level': level
                    })
                    logger.debug(f"Found word: {result.get('name')} (score: {distance:.4f})")
                elif mapping['entity_type'] == 'kanji':
                    # Use stored kanji field
                    kanji_char = mapping.get('kanji', '')
                    result.update({
                        'kanji': str(kanji_char),
                        'character': str(kanji_char),  # Also include as 'character' for compatibility
                        'meaning': str(mapping.get('meaning', '')),
                        'reading': str(mapping.get('reading', ''))
                    })
                elif mapping['entity_type'] == 'sentence':
                    result.update({
                        'japanese': str(mapping.get('japanese', '')),
                        'english': str(mapping.get('english', ''))
                    })
                
                results.append(result)
                
                # Stop if we have enough results
                if len(results) >= k:
                    break
            
            logger.info(f"Similarity search returned {len(results)} results for query '{query}' (entity_type: {entity_type})")
            if results:
                logger.info(f"Best match: {results[0].get('name', results[0].get('kanji', 'unknown'))} (score: {results[0].get('score', 0):.4f})")
            
            return results
        
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []

