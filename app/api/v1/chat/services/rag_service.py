"""
RAG service for semantic search and context retrieval
"""
import logging
from typing import List, Dict, Optional

# Try relative import first, fallback to absolute import
try:
    from integrations.vector_store import FAISSVectorStore
except ImportError:
    from app.api.v1.chat.integrations.vector_store import FAISSVectorStore

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.vector_store: Optional[FAISSVectorStore] = None
    
    def initialize(self):
        """Initialize RAG service - load FAISS index"""
        import time
        start_time = time.time()
        
        if self.vector_store:
            return  # Already initialized
        
        logger.info("Initializing RAG service...")
        
        # Load vector store
        self.vector_store = FAISSVectorStore()
        
        # Try to load from S3, fallback to building from DynamoDB
        if not self.vector_store.load_from_s3():
            logger.warning("Could not load FAISS index from S3, building from DynamoDB...")
            logger.warning("WARNING: This will take a long time if you have many items. Consider building the index first with: python scripts/build_faiss_index.py")
            self.vector_store.build_index_from_dynamodb()
            # Try to save to S3 (may fail if permissions not set, that's OK)
            try:
                self.vector_store.save_to_s3()
            except Exception as e:
                logger.warning(f"Could not save index to S3: {e}")
        
        total_time = time.time() - start_time
        logger.info(f"RAG service initialized (total time: {total_time:.2f} seconds)")
    
    def search_words(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for similar words using vector similarity
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of word results with scores
        """
        if not self.vector_store:
            self.initialize()
        
        return self.vector_store.similarity_search(query, k=k, entity_type='word')
    
    def search_kanjis(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for similar kanjis using vector similarity
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of kanji results with scores
        """
        if not self.vector_store:
            self.initialize()
        
        return self.vector_store.similarity_search(query, k=k, entity_type='kanji')
    
    def search_all(self, query: str, k: int = 5) -> Dict[str, List[Dict]]:
        """
        Search across all entity types
        
        Args:
            query: Search query
            k: Number of results per type
            
        Returns:
            Dictionary with 'words' and 'kanjis' lists
        """
        if not self.vector_store:
            self.initialize()
        
        words = self.vector_store.similarity_search(query, k=k, entity_type='word')
        kanjis = self.vector_store.similarity_search(query, k=k, entity_type='kanji')
        
        return {
            'words': words,
            'kanjis': kanjis
        }

