# Phase 3 Implementation Guide - Vector Search with RAG

## Overview

Phase 3 adds semantic search capabilities to the chatbot using vector embeddings and FAISS. This allows the chatbot to find words and kanjis even when the exact spelling doesn't match.

## What's New

1. **Vector Embeddings**: Words and kanjis are now embedded using AWS Bedrock Titan Embeddings
2. **FAISS Index**: Vector search index stored in S3 for fast similarity search
3. **Semantic Search**: Tool functions now use vector search first, falling back to exact match
4. **RAG Service**: Service layer for managing vector search operations

## Architecture

```
User Query
    ↓
Tool Function (search_word_by_name / search_kanji_by_character)
    ↓
RAG Service (semantic search)
    ↓
FAISS Vector Store (similarity search)
    ↓
Return best match or fallback to exact match
```

## Setup Steps

### 1. Deploy Infrastructure

Update and deploy the SAM template:

```bash
sam build
sam deploy
```

This will:
- Add Bedrock permissions for embeddings
- Add S3 permissions for FAISS index storage
- Increase Lambda memory to 1024MB and timeout to 300s

### 2. Generate Embeddings

Generate embeddings for all words, kanjis, and sentences:

```bash
# Generate embeddings for all entity types
python scripts/generate_embeddings.py --entity-type all

# Or generate for specific types
python scripts/generate_embeddings.py --entity-type word
python scripts/generate_embeddings.py --entity-type kanji
python scripts/generate_embeddings.py --entity-type sentence

# For testing, limit the number of items
python scripts/generate_embeddings.py --entity-type word --limit 100
```

**Note**: This script will:
- Query all items from DynamoDB
- Generate embeddings using Bedrock Titan
- Store embeddings back to DynamoDB
- Skip items that already have embeddings

### 3. Build FAISS Index

Build the FAISS index from DynamoDB embeddings:

```bash
python scripts/build_faiss_index.py
```

This will:
- Load all items with embeddings from DynamoDB
- Build FAISS index
- Save index and metadata to S3

### 4. Test Vector Search

The chatbot will now automatically use vector search when:
- User asks about a word (even with partial/spelling variations)
- User asks about a kanji (by character, meaning, or reading)

Example queries that will benefit from vector search:
- "What does konnichiwa mean?" (even if spelled slightly differently)
- "Tell me about the kanji for water" (semantic search by meaning)
- "What's the word for hello?" (semantic search by English meaning)

## How It Works

### Search Flow

1. **Vector Search First**: When a tool function is called, it first tries vector search
2. **Best Match**: Returns the most similar result (lowest distance score)
3. **Fallback**: If vector search fails or returns no results, falls back to exact match search

### Embedding Generation

- **Words**: Combines Japanese name, hiragana, English, and other language fields
- **Kanjis**: Combines kanji character, meaning, and reading
- **Sentences**: Combines Japanese and English text

### FAISS Index

- Stored in S3 at `faiss_index/index.faiss` and `faiss_index/metadata.pkl`
- Loaded on first use (cached in Lambda)
- Rebuilt when embeddings are updated

## Environment Variables

The following environment variables are automatically set:

- `S3_BUCKET_NAME`: S3 bucket for FAISS index storage
- `FAISS_INDEX_S3_KEY`: S3 key for FAISS index (default: `faiss_index/index.faiss`)
- `FAISS_INDEX_METADATA_S3_KEY`: S3 key for metadata (default: `faiss_index/metadata.pkl`)
- `AWS_REGION`: AWS region (default: `ap-northeast-1`)

## Updating Embeddings

When new words or kanjis are added:

1. **Automatic**: Embeddings can be generated automatically when items are created (future enhancement)
2. **Manual**: Run the embedding generation script:

```bash
python scripts/generate_embeddings.py --entity-type word
python scripts/build_faiss_index.py
```

## Troubleshooting

### Vector Search Not Working

1. **Check Embeddings**: Verify items have embeddings in DynamoDB
2. **Check FAISS Index**: Verify index exists in S3
3. **Check Permissions**: Verify Bedrock and S3 permissions are set
4. **Check Logs**: Look for errors in CloudWatch logs

### Slow Performance

1. **Index Size**: Large indexes may take time to load
2. **Lambda Memory**: Ensure memory is set to 1024MB or higher
3. **S3 Access**: First load may be slow if index is large

### No Results from Vector Search

1. **Index Empty**: Rebuild the FAISS index
2. **No Embeddings**: Generate embeddings first
3. **Query Too Different**: Vector search may not find matches for very different queries

## Cost Considerations

- **Bedrock Embeddings**: ~$0.0001 per 1K tokens
- **S3 Storage**: Minimal (index is typically < 100MB)
- **Lambda**: Increased memory usage (1024MB vs 256MB)

Estimated additional cost: < $1/month for typical usage

## Next Steps

After Phase 3 is working:

1. **Monitor Performance**: Check CloudWatch logs for search performance
2. **Optimize Index**: Consider incremental index updates
3. **Add More Entity Types**: Extend to sentences if needed
4. **Fine-tune Search**: Adjust similarity thresholds if needed

