# パフォーマンス問題の分析

## 問題: リクエスト処理に1分46秒かかる

### 証拠1: コードフローの確認

**`tools/dynamodb_tools.py` (15-26行目)**
```python
def get_rag_service():
    """Get or initialize RAG service"""
    global _rag_service
    if _rag_service is None:
        try:
            from services.rag_service import RAGService
            _rag_service = RAGService()
            _rag_service.initialize()  # ← ここで初期化
```

**`services/rag_service.py` (14-34行目)**
```python
def initialize(self):
    """Initialize RAG service - load FAISS index"""
    if self.vector_store:
        return  # Already initialized
    
    logger.info("Initializing RAG service...")
    
    # Load vector store
    self.vector_store = FAISSVectorStore()
    
    # Try to load from S3, fallback to building from DynamoDB
    if not self.vector_store.load_from_s3():  # ← S3から読み込み試行
        logger.warning("Could not load FAISS index from S3, building from DynamoDB...")
        self.vector_store.build_index_from_dynamodb()  # ← ここが遅い！
```

### 証拠2: 問題の根本原因

**`integrations/vector_store.py` (27-91行目)**
```python
def build_index_from_dynamodb(self):
    """
    Build FAISS index from DynamoDB embeddings
    """
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
            # ... DynamoDBから全データを読み込む
```

**問題点:**
1. **S3インデックスが存在しない場合、毎回DynamoDBから全データを読み込む**
2. **10,000単語以上の場合、すべての埋め込みを読み込むのに時間がかかる**
3. **各リクエストごとに初期化が発生する可能性がある**

### 証拠3: 追加の問題

**`integrations/vector_store.py` (17行目)**
```python
def __init__(self):
    self.embedding_service  # ← 代入されていない！
```

これは`EmbeddingService`のインスタンスが作成されていないため、エラーになる可能性があります。

## 推定される処理時間の内訳

1. **S3からの読み込み試行**: 5-10秒（タイムアウトまで待機）
2. **DynamoDBからの全データ読み込み**: 60-90秒（10,000単語以上の場合）
3. **FAISSインデックス構築**: 10-20秒
4. **その他の処理**: 5-10秒

**合計: 約80-130秒** ← 実際の1分46秒（106秒）と一致

## 解決策

1. **S3バケットを設定し、インデックスを事前に構築**
2. **`vector_store.py`の`__init__`を修正**
3. **初期化を非同期化またはキャッシュ**

