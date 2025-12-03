# AI Chatbot Implementation Plan with RAG

## Overview

Implement an AI chatbot that answers questions about the Japanese language learning app using:
- **RAG (Retrieval Augmented Generation)** with vector embeddings
- **AWS Bedrock Titan** for embeddings
- **FAISS** for vector search
- **LangChain** for orchestration
- **Gemini 2.5 Flash Live API** for real-time chat (text + voice from the start)
- **DynamoDB** for data storage and tool calls

**Budget**: 
- Base RAG Infrastructure: < $2/month ✅
- Gemini Live API: ~$0.0675 per 5-minute voice session
- **Total**: ~$2-4/month for moderate usage (30-50 voice sessions/month) ✅

**Timeline**: 16-23 days (3-4.5 weeks)

---

## Architecture: Gemini Live API from Phase 1

**Why This Architecture**:
- ✅ **Gemini Live API handles both text AND voice** - no need for separate phases
- ✅ **Much simpler**: No REST → WebSocket → Voice progression
- ✅ **Better UX**: Real-time from day one
- ✅ **Less code**: One API for everything
- ✅ **Native GCP integration**: You're already using Gemini API
- ✅ **Built-in features**: VAD, turn-taking, interrupts, tool use

**Gemini 2.5 Flash Live API Features**:
- ✅ Real-time audio streaming (PCM 16kHz input, 24kHz output)
- ✅ Video support (1 FPS streaming)
- ✅ Text input/output
- ✅ Affective dialog (adapts to user expression)
- ✅ Automatic VAD and turn-taking
- ✅ Function Calling support (for DynamoDB tools)
- ✅ Google Search Grounding (optional)
- ✅ WebSocket protocol (WSS) for low-latency bidirectional streaming

---

## Phase 1: Infrastructure Setup

### Step 1.1: Set Up Gemini 2.5 Flash Live API
**Objective**: Configure Gemini Live API access via Vertex AI

**Tasks**:
1. Enable Vertex AI API in GCP Console
2. Verify Gemini 2.5 Flash Live API availability in your region
3. Set up GCP service account with Vertex AI permissions
4. Create service account key (JSON) for Lambda
5. Store service account key securely (AWS Secrets Manager or environment variable)
6. Test basic connection to Gemini Live API

**Test Criteria**:
- ✅ Vertex AI API is enabled
- ✅ Gemini Live API is available in your region
- ✅ Service account has correct permissions
- ✅ Can establish WebSocket connection to Gemini Live API
- ✅ Can send/receive test messages

**Files to Create**:
- `app/api/v1/chat/integrations/gemini_live_client.py`

**Test Command**:
```python
from app.api.v1.chat.integrations.gemini_live_client import GeminiLiveClient
client = GeminiLiveClient()
client.connect()
client.send_message("Hello")
response = client.receive_message()
assert response is not None
```

**Rollback**: Disable Vertex AI API if needed

---

### Step 1.2: Enable AWS Bedrock Access (For RAG Embeddings)
**Objective**: Set up access to Bedrock Titan embeddings

**Tasks**:
1. Enable Bedrock service in AWS Console
2. Request access to `amazon.titan-embed-text-v1` model
3. Verify access via AWS CLI

**Test Criteria**:
- ✅ Bedrock service is enabled
- ✅ Titan embeddings model is accessible
- ✅ Can generate test embedding via AWS CLI

**Files to Modify**:
- None (AWS Console/CLI only)

**Test Command**:
```bash
aws bedrock-runtime invoke-model \
  --model-id amazon.titan-embed-text-v1 \
  --body '{"inputText":"test"}' \
  --region us-east-1 \
  output.json
```

**Rollback**: Disable Bedrock access if needed

---

### Step 1.3: Add Dependencies
**Objective**: Install required Python packages

**Tasks**:
1. Add LangChain packages to requirements.txt
2. Add FAISS and Bedrock integration packages
3. Add Gemini Live API packages
4. Update Lambda package configuration

**Test Criteria**:
- ✅ All packages install successfully
- ✅ No import errors
- ✅ Package size within Lambda limits (< 250MB)

**Files to Modify**:
- `app/api/v1/chat/requirements.txt` (new file)

**Dependencies to Add**:
```txt
langchain>=0.1.0
langchain-aws>=0.1.0
langchain-community>=0.0.20
faiss-cpu>=1.7.4
boto3>=1.28.0
google-cloud-aiplatform>=1.38.0  # For Gemini Live API
google-generativeai>=0.3.0  # You may already have this
websockets>=12.0  # For WebSocket connection
```

**Test Command**:
```bash
pip install -r app/api/v1/chat/requirements.txt
python -c "import langchain; import faiss; import google.cloud.aiplatform; print('OK')"
```

**Rollback**: Remove packages from requirements.txt

---

### Step 1.4: Configure IAM Permissions (AWS)
**Objective**: Grant Lambda access to Bedrock, S3, DynamoDB, and Secrets Manager

**Tasks**:
1. Add Bedrock invoke permissions to Lambda IAM role
2. Add S3 read/write permissions for FAISS index
3. Add Secrets Manager read permissions (for GCP service account key)
4. Verify existing DynamoDB permissions

**Test Criteria**:
- ✅ IAM policies are created
- ✅ Lambda function has correct permissions
- ✅ Can verify permissions in IAM console

**Files to Modify**:
- `template.yaml` (add IAM policies to ChatFunction)

**Test Command**:
```bash
aws iam get-role-policy --role-name <role-name> --policy-name <policy-name>
```

**Rollback**: Remove IAM policies

---

## Phase 2: Embedding Generation and Storage

### Step 2.1: Create Embedding Generation Script
**Objective**: Generate embeddings for existing data

**Tasks**:
1. Create script to read all words, kanjis, sentences from DynamoDB
2. Generate embeddings using Bedrock Titan
3. Store embeddings in DynamoDB as new attribute
4. Add progress tracking and error handling
5. Support batch processing

**Test Criteria**:
- ✅ Can generate embeddings for sample data
- ✅ Embeddings are stored in DynamoDB
- ✅ Embedding dimension is correct (1536 for Titan)
- ✅ Batch processing works correctly
- ✅ Error handling works for failed embeddings

**Files to Create**:
- `scripts/generate_embeddings.py`

**Test Command**:
```bash
# Test with small subset
python scripts/generate_embeddings.py --limit 10 --entity-type word

# Full generation
python scripts/generate_embeddings.py
```

**Rollback**: Remove embedding attribute from DynamoDB items

---

### Step 2.2: Create Embedding Update Hook
**Objective**: Automatically generate embeddings when data changes

**Tasks**:
1. Create service to generate embedding on item create/update
2. Integrate with existing word/kanji/sentence endpoints
3. Handle errors gracefully (don't fail if embedding fails)

**Test Criteria**:
- ✅ Embedding generated when new word is created
- ✅ Embedding updated when word is modified
- ✅ Errors don't break main functionality

**Files to Create**:
- `app/api/v1/chat/services/embedding_service.py`

**Files to Modify**:
- `app/api/v1/words/endpoints/word.py` (add embedding generation)
- `app/api/v1/kanjis/endpoints/kanji.py` (add embedding generation)
- `app/api/v1/sentences/endpoints/sentence.py` (add embedding generation)

**Test Method**:
1. Create new word via API
2. Verify embedding is generated and stored
3. Update word
4. Verify embedding is updated

**Rollback**: Remove embedding generation calls

---

## Phase 3: FAISS Index Creation

### Step 3.1: Create FAISS Index Builder
**Objective**: Build FAISS index from DynamoDB embeddings

**Tasks**:
1. Create script to read embeddings from DynamoDB
2. Build FAISS index with proper ID mapping
3. Save index to S3 for caching
4. Support incremental updates

**Test Criteria**:
- ✅ FAISS index is created successfully
- ✅ Index contains all items with embeddings
- ✅ ID mapping is correct
- ✅ Index is saved to S3
- ✅ Can load index from S3

**Files to Create**:
- `scripts/build_faiss_index.py`
- `app/api/v1/chat/integrations/vector_store.py`

**Test Command**:
```bash
# Build index
python scripts/build_faiss_index.py

# Verify index
python -c "from app.api.v1.chat.integrations.vector_store import FAISSVectorStore; vs = FAISSVectorStore(); vs.load_from_s3(); print('Index loaded:', vs.vector_store.ntotal)"
```

**Rollback**: Delete S3 index files

---

### Step 3.2: Implement Index Loading in Lambda
**Objective**: Load FAISS index on Lambda cold start

**Tasks**:
1. Implement index loading from S3
2. Cache index in Lambda memory
3. Handle missing index (rebuild from DynamoDB)
4. Optimize for cold start time

**Test Criteria**:
- ✅ Index loads from S3 on cold start
- ✅ Load time is acceptable (< 2 seconds)
- ✅ Falls back to DynamoDB if S3 missing
- ✅ Index persists across warm invocations

**Files to Modify**:
- `app/api/v1/chat/integrations/vector_store.py`

**Test Method**:
1. Deploy Lambda function
2. Invoke function (cold start)
3. Check CloudWatch logs for load time
4. Verify index is usable

**Rollback**: Remove index loading, use DynamoDB only

---

## Phase 4: LangChain Integration

### Step 4.1: Set Up LangChain Bedrock Embeddings
**Objective**: Configure LangChain to use Bedrock Titan

**Tasks**:
1. Create BedrockEmbeddings wrapper
2. Configure region and model ID
3. Add error handling and retry logic
4. Test embedding generation

**Test Criteria**:
- ✅ Can generate embeddings via LangChain
- ✅ Embeddings match direct Bedrock calls
- ✅ Error handling works
- ✅ Retry logic works for transient errors

**Files to Create**:
- `app/api/v1/chat/integrations/bedrock_embeddings.py`

**Test Command**:
```python
from app.api.v1.chat.integrations.bedrock_embeddings import BedrockEmbeddingService
service = BedrockEmbeddingService()
embedding = service.embed_query("test")
assert len(embedding) == 1536
```

**Rollback**: Remove LangChain, use direct Bedrock calls

---

### Step 4.2: Create LangChain FAISS Vector Store
**Objective**: Integrate FAISS with LangChain

**Tasks**:
1. Create FAISS vector store using LangChain
2. Implement save/load from S3
3. Create Document objects from DynamoDB items
4. Test similarity search

**Test Criteria**:
- ✅ Can create FAISS index with LangChain
- ✅ Can save/load from S3
- ✅ Similarity search returns correct results
- ✅ Results include metadata (IDs, text)

**Files to Modify**:
- `app/api/v1/chat/integrations/vector_store.py`

**Test Command**:
```python
from app.api.v1.chat.integrations.vector_store import FAISSVectorStore
vs = FAISSVectorStore()
vs.load_from_s3()
results = vs.similarity_search("こんにちは", k=5)
assert len(results) > 0
```

**Rollback**: Use direct FAISS without LangChain

---

### Step 4.3: Create RAG Chain
**Objective**: Build RAG pipeline with LangChain

**Tasks**:
1. Create ConversationalRetrievalChain
2. Configure retriever with FAISS
3. Set up conversation memory
4. Create custom prompt template
5. Test end-to-end RAG flow

**Test Criteria**:
- ✅ RAG chain is created successfully
- ✅ Retrieves relevant context
- ✅ Generates appropriate responses
- ✅ Conversation memory works
- ✅ Response quality is good

**Files to Create**:
- `app/api/v1/chat/services/rag_service.py`

**Test Command**:
```python
from app.api.v1.chat.services.rag_service import RAGService
service = RAGService()
service.initialize_chain()
response = service.chat("What does こんにちは mean?")
assert len(response["answer"]) > 0
```

**Rollback**: Remove RAG chain, use simple retrieval

---

## Phase 5: DynamoDB Tool Functions

### Step 5.1: Create Tool Functions for LangChain
**Objective**: Enable tool calling to DynamoDB

**Tasks**:
1. Create `search_words` tool function
2. Create `get_word_details` tool function
3. Create `get_kanji_details` tool function
4. Create `get_sentence_details` tool function
5. Register tools with LangChain

**Test Criteria**:
- ✅ All tool functions are created
- ✅ Tools can be called successfully
- ✅ Tools return correct data format
- ✅ Tools are registered with LangChain
- ✅ LLM can invoke tools correctly

**Files to Create**:
- `app/api/v1/chat/tools/dynamodb_tools.py`

**Test Command**:
```python
from app.api.v1.chat.tools.dynamodb_tools import search_words
result = search_words.invoke({"query": "こんにちは", "language": "en"})
assert len(result) > 0
```

**Rollback**: Remove tool functions

---

### Step 5.2: Create User Progress & Plan Tool Functions
**Objective**: Enable chatbot to access user's learning progress and plans

**Tasks**:
1. Create `get_user_progress` tool function
   - Get user's learning progress for words, sentences, or kana
   - Support level filtering (N5, N4, N3, N2, N1 groups)
   - Returns: learned, unlearned, reviewable counts per level
2. Create `get_user_plan` tool function
   - Get user's learning plan (review schedule by 24-hour time slots)
   - Returns: List of time slots with review counts
3. Create `get_user_learned_items` tool function
   - Get list of items user has learned
   - Support level filtering
   - Returns: Learned items with proficiency scores
4. Create `get_user_reviewable_items` tool function
   - Get items ready for review (next_datetime <= now)
   - Support limit parameter
   - Returns: List of reviewable items with details
5. Integrate with existing progress/plan DynamoDB clients
6. Add user authentication/authorization checks
7. Register tools with LangChain

**Test Criteria**:
- ✅ All user progress/plan tool functions are created
- ✅ Tools can be called successfully with user_id
- ✅ Tools return correct data format
- ✅ User authentication works (only own data accessible)
- ✅ Tools are registered with LangChain
- ✅ LLM can invoke tools correctly

**Files to Create**:
- `app/api/v1/chat/tools/user_progress_tools.py`

**Files to Modify**:
- `app/api/v1/chat/tools/dynamodb_tools.py` (import and register new tools)

**Test Command**:
```python
from app.api.v1.chat.tools.user_progress_tools import get_user_progress
result = get_user_progress.invoke({
    "user_id": "test-user-123",
    "entity_type": "words",
    "group": "N5"
})
assert "learned" in result
assert "unlearned" in result
```

**Rollback**: Remove user progress tool functions

---

### Step 5.3: Integrate Tools with Gemini Live API
**Objective**: Enable Function Calling with Gemini Live API

**Tasks**:
1. Register Function Calling tools with Gemini Live API
2. Configure tool descriptions (search_words, get_word_details, etc.)
3. Test tool invocation during live session
4. Handle tool execution errors
5. Pass tool results back to Gemini Live API
6. Use Google Search Grounding (optional) for additional context

**Test Criteria**:
- ✅ Gemini Live API can see available tools
- ✅ Gemini Live API invokes tools when appropriate
- ✅ Tool results are used in response
- ✅ Error handling works
- ✅ Tools work in both text and voice modes

**Files to Modify**:
- `app/api/v1/chat/services/gemini_live_rag_service.py`

**Test Method**:
1. Ask question requiring tool call via Gemini Live API
2. Verify tool is invoked
3. Verify response includes tool data

**Rollback**: Disable tool calling

---

## Phase 6: Gemini Live API Integration (Text + Voice from Start)

### Step 6.1: Integrate Gemini Live API with RAG
**Objective**: Connect Gemini Live API to RAG system

**Tasks**:
1. Set up Gemini Live API WebSocket connection (WSS)
2. Integrate with existing RAG service
3. Inject RAG context into Live API sessions
4. Handle bidirectional audio/text streaming
5. Configure tool use (Function Calling) for DynamoDB queries
6. Support both text and voice input/output

**Test Criteria**:
- ✅ Gemini Live API connection works
- ✅ RAG context is retrieved and injected
- ✅ Responses use RAG context
- ✅ Works with text input
- ✅ Works with voice input (audio streaming)
- ✅ Tool calling works (DynamoDB queries)

**Files to Create**:
- `app/api/v1/chat/services/gemini_live_rag_service.py`
- `app/api/v1/chat/integrations/gemini_live_client.py`

**Test Command**:
```python
from app.api.v1.chat.services.gemini_live_rag_service import GeminiLiveRAGService
service = GeminiLiveRAGService()
# Connect and test
service.connect()
service.send_message("What does こんにちは mean?")
response = service.receive_response()
# Test voice
service.send_audio(audio_chunk)
response_audio = service.receive_audio()
```

**Rollback**: Use Gemini Live API without RAG (fallback)

---

### Step 6.2: Set Up WebSocket Handler for Gemini Live API
**Objective**: Handle WebSocket connections via API Gateway WebSocket API

**Architecture Note**: 
- **API Gateway WebSocket API** manages the WebSocket connection lifecycle
- **Lambda** handles individual events ($connect, $disconnect, $default)
- **Gemini Live API** maintains its own WebSocket connection (WSS) from Lambda to Google

**Tasks**:
1. **Create Lambda Handler for API Gateway WebSocket Events**
   - Handle `$connect` event (store connection in DynamoDB)
   - Handle `$disconnect` event (clean up connection state)
   - Handle `$default` event (process incoming messages)
   - Extract user_id from connection query string or headers

2. **Create Connection Manager**
   - Store connection state in DynamoDB (connectionId, user_id, timestamp)
   - Track active connections per user
   - Handle connection cleanup on disconnect
   - Implement TTL for stale connections

3. **Create Gemini Live API Client Wrapper**
   - Maintain WebSocket connection from Lambda to Gemini Live API
   - Bridge between API Gateway WebSocket and Gemini Live API WebSocket
   - Handle bidirectional message forwarding
   - Manage Gemini Live API connection lifecycle

4. **Handle Message Routing**
   - Receive message from client via API Gateway WebSocket
   - Forward to Gemini Live API (with RAG context)
   - Receive response from Gemini Live API
   - Send response back to client via API Gateway WebSocket

5. **Integrate with RAG Service**
   - Call RAG service to retrieve context
   - Inject context into Gemini Live API session
   - Handle tool calls from Gemini Live API

6. **Handle Reconnection Logic**
   - Detect disconnections
   - Re-establish Gemini Live API connection if needed
   - Restore conversation context

**Test Criteria**:
- ✅ API Gateway WebSocket connection works
- ✅ Lambda handles $connect, $disconnect, $default events
- ✅ Messages are received correctly from client
- ✅ Messages are forwarded to Gemini Live API
- ✅ Responses are sent back to client correctly
- ✅ RAG context is injected
- ✅ Connection state is managed in DynamoDB
- ✅ Reconnection works

**Files to Create**:
- `app/api/v1/chat/app.py` (Lambda handler for API Gateway WebSocket)
- `app/api/v1/chat/websocket/gemini_live_handler.py` (Gemini Live API client)
- `app/api/v1/chat/websocket/connection_manager.py` (Connection state management)

**Lambda Handler Structure**:
```python
# app/api/v1/chat/app.py
import json
import boto3
from websocket.gemini_live_handler import GeminiLiveHandler
from websocket.connection_manager import ConnectionManager

dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.getenv('CONNECTIONS_TABLE_NAME'))
connection_manager = ConnectionManager(connections_table)

def lambda_handler(event, context):
    """
    Handle API Gateway WebSocket events
    
    Event structure:
    {
        "requestContext": {
            "routeKey": "$connect" | "$disconnect" | "$default",
            "connectionId": "abc123",
            "domainName": "xxx.execute-api.region.amazonaws.com",
            "stage": "prod",
            "identity": {
                "sourceIp": "1.2.3.4"
            }
        },
        "body": "..." (for $default route, contains message from client),
        "queryStringParameters": {...} (for $connect, may contain auth token)
    }
    """
    route_key = event.get("requestContext", {}).get("routeKey")
    connection_id = event.get("requestContext", {}).get("connectionId")
    
    if route_key == "$connect":
        # Extract user_id from query string or headers
        query_params = event.get("queryStringParameters") or {}
        auth_token = query_params.get("token") or event.get("headers", {}).get("Authorization")
        user_id = extract_user_id_from_token(auth_token)
        
        # Store connection in DynamoDB
        connection_manager.save_connection(connection_id, user_id)
        
        # Initialize Gemini Live API connection
        gemini_handler = GeminiLiveHandler(connection_id, user_id)
        gemini_handler.connect()
        
        return {"statusCode": 200}
    
    elif route_key == "$disconnect":
        # Clean up connection
        connection_manager.delete_connection(connection_id)
        
        # Close Gemini Live API connection
        gemini_handler = GeminiLiveHandler.get_handler(connection_id)
        if gemini_handler:
            gemini_handler.disconnect()
        
        return {"statusCode": 200}
    
    elif route_key == "$default":
        # Get connection info
        connection = connection_manager.get_connection(connection_id)
        if not connection:
            return {"statusCode": 403, "body": "Connection not found"}
        
        user_id = connection.get("user_id")
        body = json.loads(event.get("body", "{}"))
        
        # Get or create Gemini Live API handler
        gemini_handler = GeminiLiveHandler.get_or_create(connection_id, user_id)
        
        # Process message
        message = body.get("message")
        message_type = body.get("type", "text")  # "text" or "audio"
        
        # Forward to Gemini Live API and get response
        response = gemini_handler.send_message(message, message_type)
        
        # Send response back to client via API Gateway Management API
        send_to_client(connection_id, response)
        
        return {"statusCode": 200}
    
    return {"statusCode": 500}

def send_to_client(connection_id, message):
    """Send message to client via API Gateway Management API"""
    api_gateway_management = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
    )
    api_gateway_management.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(message)
    )
```

**Test Method**:
1. Deploy Lambda function and WebSocket API
2. Connect via WebSocket (wscat or client app)
3. Verify connection stored in DynamoDB
4. Send text message
5. Verify message forwarded to Gemini Live API
6. Verify response sent back to client
7. Test voice input (audio chunks)
8. Disconnect and verify cleanup
9. Test reconnection

**Rollback**: Use REST API fallback

---

### Step 6.3: Configure RAG Context Injection
**Objective**: Inject RAG-retrieved context into Gemini Live API

**Tasks**:
1. Retrieve context using existing RAG system
2. Format context for Gemini Live API
3. Inject context at session start (system instructions)
4. Update context during conversation (if needed)
5. Use Google Search Grounding (optional) for additional context
6. Optimize context size for Live API

**Test Criteria**:
- ✅ Context is retrieved correctly
- ✅ Context is formatted properly
- ✅ Gemini Live API uses context in responses
- ✅ Context improves answer quality
- ✅ Tool use (Function Calling) works with context

**Files to Modify**:
- `app/api/v1/chat/services/gemini_live_rag_service.py`

**Test Method**:
1. Ask question about Japanese word
2. Verify RAG context is retrieved
3. Verify context is injected into Gemini Live API
4. Verify response is accurate and uses context
5. Test tool calling (DynamoDB queries)

**Rollback**: Use Gemini Live API without RAG context

---

### Step 6.4: Inject User Context at Session Start
**Objective**: Provide user's learning progress and plan context to chatbot

**Tasks**:
1. Create `get_user_context` function
   - Extract user_id from authentication token
   - Get user's progress summary (words, sentences, kana)
   - Get user's learning plan (review schedule)
   - Get user settings (base_level, preferred language, etc.)
2. Format user context as system instructions
   - Include current level progress
   - Include review schedule
   - Include learning goals/preferences
3. Inject user context at Gemini Live API session start
4. Update user context during conversation (if progress changes)
5. Ensure user context is included in RAG retrieval decisions

**Test Criteria**:
- ✅ User context is retrieved correctly
- ✅ User context is formatted properly
- ✅ User context is injected at session start
- ✅ Chatbot uses user context in responses
- ✅ Chatbot can answer questions about user progress
- ✅ Privacy: Only user's own data is accessible

**Files to Create**:
- `app/api/v1/chat/services/user_context_service.py`

**Files to Modify**:
- `app/api/v1/chat/services/gemini_live_rag_service.py` (add user context injection)
- `app/api/v1/chat/websocket/gemini_live_handler.py` (extract user_id from auth)

**Test Method**:
1. Start chat session with authenticated user
2. Verify user context is retrieved and injected
3. Ask "What words should I review today?"
4. Verify chatbot uses user progress data
5. Ask "How is my progress in N5?"
6. Verify chatbot accesses user progress correctly

**Example User Context Format**:
```
User Learning Context:
- Current Level Progress:
  * Level 1: 45/100 words learned, 12 reviewable
  * Level 2: 30/150 words learned, 8 reviewable
- Review Schedule:
  * Today (slot 0): 12 words ready for review
  * Tomorrow (slot 1): 18 words scheduled
  * This week (slot 2-7): 45 words scheduled
- User Settings:
  * Base Level: 1
  * Preferred Language: English
- Focus: Recommend items at user's current level or items needing review
```

**Rollback**: Remove user context injection, use generic context only

---

### Step 6.5: Add to SAM Template
**Objective**: Deploy chat function to AWS with WebSocket API Gateway

**Tasks**:
1. **Create WebSocket API Gateway**
   - Define WebSocket API in template.yaml
   - Configure routes: `$connect`, `$disconnect`, `$default`
   - Set route selection expression
   - Configure CORS if needed

2. **Add ChatFunction Lambda**
   - Create Lambda function for WebSocket handling
   - Configure memory (512MB - 1GB for FAISS index)
   - Set timeout (15 minutes max, but WebSocket messages are short-lived)
   - Add environment variables:
     - GCP service account key path
     - DynamoDB table name
     - S3 bucket name (for FAISS index)
     - Gemini Live API configuration

3. **Configure WebSocket Routes**
   - `$connect`: Handle new WebSocket connections
   - `$disconnect`: Clean up connection state
   - `$default`: Handle incoming messages (text/voice)

4. **Set Up Connection State Management**
   - Store connection IDs in DynamoDB
   - Track user_id per connection
   - Handle connection lifecycle

5. **Configure IAM Permissions**
   - Bedrock invoke (for embeddings)
   - DynamoDB read/write (for data and connection state)
   - S3 read (for FAISS index)
   - Secrets Manager read (for GCP credentials)

6. **Configure Lambda Layers (if needed)**
   - For large dependencies (LangChain, FAISS)
   - Keep package size under 250MB

**Test Criteria**:
- ✅ Function is deployed
- ✅ WebSocket API Gateway is created
- ✅ WebSocket routes are configured correctly
- ✅ Environment variables are set
- ✅ Permissions are correct
- ✅ Function can handle WebSocket connections
- ✅ Connection state is managed correctly

**Files to Modify**:
- `template.yaml`

**SAM Template Configuration Example**:
```yaml
# WebSocket API Gateway
ChatWebSocketApi:
  Type: AWS::ApiGatewayV2::Api
  Properties:
    Name: !Sub "${AWS::StackName}-chat-websocket"
    ProtocolType: WEBSOCKET
    RouteSelectionExpression: "$request.body.action"
    Description: "WebSocket API for Gemini Live API chat"
    CorsConfiguration:
      AllowOrigins:
        - "*"
      AllowMethods:
        - "*"
      AllowHeaders:
        - "*"

# WebSocket Deployment
ChatWebSocketDeployment:
  Type: AWS::ApiGatewayV2::Deployment
  DependsOn:
    - ChatConnectRoute
    - ChatDisconnectRoute
    - ChatDefaultRoute
  Properties:
    ApiId: !Ref ChatWebSocketApi

# WebSocket Stage
ChatWebSocketStage:
  Type: AWS::ApiGatewayV2::Stage
  Properties:
    ApiId: !Ref ChatWebSocketApi
    DeploymentId: !Ref ChatWebSocketDeployment
    StageName: !Sub "${AWS::StackName}-chat"
    DefaultRouteSettings:
      ThrottlingBurstLimit: 100
      ThrottlingRateLimit: 50
    RouteSettings:
      - RouteKey: "$default"
        ThrottlingBurstLimit: 200
        ThrottlingRateLimit: 100

# Chat Lambda Function
ChatFunction:
  Type: AWS::Serverless::Function
  Metadata:
    BuildMethod: python3.11
    BuildProperties:
      UseContainer: true
      ProjectPath: ./app/api/v1/chat
      InstallDependencies: true
  Properties:
    FunctionName: !Sub "${AWS::StackName}-ChatFunction"
    CodeUri: ./app/api/v1/chat
    Handler: app.lambda_handler
    Description: "Lambda function for AI chatbot with Gemini Live API"
    Runtime: python3.11
    MemorySize: 1024  # 1GB for FAISS index
    Timeout: 300  # 5 minutes (sufficient for WebSocket messages)
    Environment:
      Variables:
        DYNAMODB_TABLE_NAME: !Ref DynamoDBTable
        S3_BUCKET_NAME: !Ref S3BucketName
        GCP_SERVICE_ACCOUNT_KEY: !Ref GcpServiceAccountKey  # From Secrets Manager
        GEMINI_LIVE_API_ENDPOINT: "https://generativelanguage.googleapis.com"
        FAISS_INDEX_S3_KEY: "faiss_index"
        LOG_LEVEL: INFO
    Events:
      Connect:
        Type: WebSocket
        Properties:
          Api: !Ref ChatWebSocketApi
          Route: $connect
      Disconnect:
        Type: WebSocket
        Properties:
          Api: !Ref ChatWebSocketApi
          Route: $disconnect
      Default:
        Type: WebSocket
        Properties:
          Api: !Ref ChatWebSocketApi
          Route: $default
    Policies:
      - Statement:
        - Effect: Allow
          Action:
            - bedrock:InvokeModel
          Resource:
            - !Sub "arn:aws:bedrock:${AWS::Region}::foundation-model/amazon.titan-embed-text-v1"
        - Effect: Allow
          Action:
            - dynamodb:GetItem
            - dynamodb:PutItem
            - dynamodb:UpdateItem
            - dynamodb:DeleteItem
            - dynamodb:Query
            - dynamodb:Scan
          Resource:
            - !Sub "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}"
            - !Sub "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*"
        - Effect: Allow
          Action:
            - s3:GetObject
            - s3:ListBucket
          Resource:
            - !Sub "arn:aws:s3:::${S3BucketName}"
            - !Sub "arn:aws:s3:::${S3BucketName}/*"
        - Effect: Allow
          Action:
            - secretsmanager:GetSecretValue
          Resource:
            - !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:${GcpServiceAccountKey}*"

# Connection State DynamoDB Table (optional, for connection management)
ChatConnectionsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub "${AWS::StackName}-chat-connections"
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: connectionId
        AttributeType: S
    KeySchema:
      - AttributeName: connectionId
        KeyType: HASH
    TimeToLiveSpecification:
      AttributeName: ttl
      Enabled: true
    Tags:
      - Key: Environment
        Value: !Sub "${AWS::StackName}"

# WebSocket Routes
ChatConnectRoute:
  Type: AWS::ApiGatewayV2::Route
  Properties:
    ApiId: !Ref ChatWebSocketApi
    RouteKey: $connect
    Target: !Sub "integrations/${ChatConnectIntegration}"

ChatDisconnectRoute:
  Type: AWS::ApiGatewayV2::Route
  Properties:
    ApiId: !Ref ChatWebSocketApi
    RouteKey: $disconnect
    Target: !Sub "integrations/${ChatDisconnectIntegration}"

ChatDefaultRoute:
  Type: AWS::ApiGatewayV2::Route
  Properties:
    ApiId: !Ref ChatWebSocketApi
    RouteKey: $default
    Target: !Sub "integrations/${ChatDefaultIntegration}"

# WebSocket Integrations
ChatConnectIntegration:
  Type: AWS::ApiGatewayV2::Integration
  Properties:
    ApiId: !Ref ChatWebSocketApi
    IntegrationType: AWS_PROXY
    IntegrationUri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ChatFunction.Arn}/invocations"

ChatDisconnectIntegration:
  Type: AWS::ApiGatewayV2::Integration
  Properties:
    ApiId: !Ref ChatWebSocketApi
    IntegrationType: AWS_PROXY
    IntegrationUri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ChatFunction.Arn}/invocations"

ChatDefaultIntegration:
  Type: AWS::ApiGatewayV2::Integration
  Properties:
    ApiId: !Ref ChatWebSocketApi
    IntegrationType: AWS_PROXY
    IntegrationUri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ChatFunction.Arn}/invocations"

# Lambda Permission for WebSocket API
ChatFunctionWebSocketPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref ChatFunction
    Action: lambda:InvokeFunction
    Principal: apigateway.amazonaws.com
    SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${ChatWebSocketApi}/*/*"
```

**Lambda Handler Structure**:
```python
# app/api/v1/chat/app.py
from mangum import Mangum
from fastapi import FastAPI
import json

app = FastAPI()

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    # WebSocket handling logic
    pass

# For WebSocket API Gateway, we need a Lambda handler
def lambda_handler(event, context):
    """
    Handle WebSocket API Gateway events
    Event structure:
    {
        "requestContext": {
            "routeKey": "$connect" | "$disconnect" | "$default",
            "connectionId": "abc123",
            "domainName": "xxx.execute-api.region.amazonaws.com",
            "stage": "prod"
        },
        "body": "..." (for $default route)
    }
    """
    route_key = event.get("requestContext", {}).get("routeKey")
    connection_id = event.get("requestContext", {}).get("connectionId")
    
    if route_key == "$connect":
        # Store connection in DynamoDB
        # Extract user_id from query string or headers
        return {"statusCode": 200}
    
    elif route_key == "$disconnect":
        # Clean up connection from DynamoDB
        return {"statusCode": 200}
    
    elif route_key == "$default":
        # Handle incoming message
        # Process with Gemini Live API
        # Return response
        return {"statusCode": 200}
    
    return {"statusCode": 500}
```

**Test Command**:
```bash
sam build
sam deploy --guided
```

**WebSocket Connection Test**:
```bash
# Get WebSocket URL from deployment output
WS_URL="wss://<api-id>.execute-api.<region>.amazonaws.com/<stage>"

# Test connection (using wscat or similar)
wscat -c $WS_URL

# Send test message
{"action": "chat", "message": "Hello"}
```

**Rollback**: Remove function and WebSocket API from template

---

## Phase 7: Testing and Validation

### Step 7.1: Unit Tests
**Objective**: Test individual components

**Tasks**:
1. Test embedding generation
2. Test FAISS index building
3. Test vector search
4. Test tool functions
5. Test RAG service
6. Test Gemini Live API client

**Test Criteria**:
- ✅ All unit tests pass
- ✅ Code coverage > 80%
- ✅ Edge cases are handled

**Files to Create**:
- `app/api/v1/chat/tests/test_embeddings.py`
- `app/api/v1/chat/tests/test_vector_store.py`
- `app/api/v1/chat/tests/test_rag_service.py`
- `app/api/v1/chat/tests/test_tools.py`
- `app/api/v1/chat/tests/test_gemini_live_client.py`

**Test Command**:
```bash
pytest app/api/v1/chat/tests/ -v
```

**Rollback**: Fix failing tests

---

### Step 7.2: Integration Tests
**Objective**: Test end-to-end functionality

**Tasks**:
1. Test complete RAG flow
2. Test tool calling
3. Test conversation memory
4. Test error scenarios
5. Test with real DynamoDB data
6. Test Gemini Live API integration

**Test Criteria**:
- ✅ All integration tests pass
- ✅ RAG returns relevant results
- ✅ Tool calling works correctly
- ✅ Memory persists across messages
- ✅ Gemini Live API works with RAG

**Files to Create**:
- `app/api/v1/chat/tests/test_integration.py`

**Test Command**:
```bash
pytest app/api/v1/chat/tests/test_integration.py -v
```

**Rollback**: Fix integration issues

---

### Step 7.3: Performance Testing
**Objective**: Verify performance meets requirements

**Tasks**:
1. Test cold start time
2. Test warm invocation time
3. Test embedding generation time
4. Test vector search time
5. Test end-to-end latency
6. Test Gemini Live API latency

**Test Criteria**:
- ✅ Cold start < 5 seconds
- ✅ Warm invocation < 2 seconds
- ✅ Embedding generation < 500ms
- ✅ Vector search < 100ms
- ✅ End-to-end < 3 seconds
- ✅ Voice response latency < 1 second (first audio chunk)

**Files to Create**:
- `scripts/performance_test.py`

**Test Command**:
```bash
python scripts/performance_test.py
```

**Rollback**: Optimize slow components

---

### Step 7.4: Cost Validation
**Objective**: Verify costs stay under budget

**Tasks**:
1. Monitor Bedrock embedding costs
2. Monitor Lambda execution costs
3. Monitor DynamoDB read costs
4. Monitor S3 storage costs
5. Monitor Gemini Live API usage costs
6. Calculate monthly estimate

**Test Criteria**:
- ✅ Embedding costs < $1/month (for 100K queries)
- ✅ Lambda costs < $0.50/month
- ✅ DynamoDB costs < $0.50/month
- ✅ S3 costs < $0.10/month
- ✅ Gemini Live API costs < $2-4/month (30-50 voice sessions)
- ✅ Total < $4-6/month

**Test Method**:
1. Run load test (1000 queries)
2. Check AWS Cost Explorer
3. Check GCP Billing
4. Calculate monthly projection

**Rollback**: Optimize to reduce costs

---

## Phase 8: Quality Improvements

### Step 8.1: Response Quality Testing
**Objective**: Ensure chatbot provides accurate, helpful responses

**Tasks**:
1. Test with 50+ sample questions
2. Evaluate answer accuracy
3. Check for hallucinations
4. Verify context relevance
5. Test multi-turn conversations
6. Test voice conversation quality

**Test Criteria**:
- ✅ Answers are accurate (> 90%)
- ✅ No significant hallucinations
- ✅ Context is relevant
- ✅ Multi-turn conversations work
- ✅ Voice responses are natural
- ✅ User satisfaction is high

**Files to Create**:
- `scripts/test_response_quality.py`
- `test_questions.json` (50+ test questions)

**Test Command**:
```bash
python scripts/test_response_quality.py
```

**Rollback**: Improve prompts and retrieval

---

### Step 8.2: Prompt Engineering
**Objective**: Optimize prompts for better responses

**Tasks**:
1. Refine system prompt
2. Optimize context formatting
3. Add examples to prompt
4. Test different prompt variations
5. A/B test prompt effectiveness

**Test Criteria**:
- ✅ Responses are more accurate
- ✅ Responses are more helpful
- ✅ Responses are more concise
- ✅ User satisfaction improves

**Files to Modify**:
- `app/api/v1/chat/services/rag_service.py` (prompt template)
- `app/api/v1/chat/services/gemini_live_rag_service.py` (system instructions)

**Test Method**:
1. Test with same questions
2. Compare response quality
3. Select best prompt

**Rollback**: Revert to previous prompt

---

### Step 8.3: Error Handling and Edge Cases
**Objective**: Handle errors gracefully

**Tasks**:
1. Handle missing embeddings
2. Handle empty search results
3. Handle tool execution errors
4. Handle LLM errors
5. Handle Gemini Live API connection errors
6. Add fallback responses

**Test Criteria**:
- ✅ All error cases are handled
- ✅ User-friendly error messages
- ✅ System doesn't crash
- ✅ Fallbacks work correctly

**Files to Modify**:
- `app/api/v1/chat/services/rag_service.py`
- `app/api/v1/chat/services/gemini_live_rag_service.py`
- `app/api/v1/chat/endpoints/chat.py`

**Test Method**:
1. Test each error scenario
2. Verify graceful handling
3. Check error messages

**Rollback**: Add more error handling

---

## Phase 9: Deployment and Monitoring

### Step 9.1: Deploy to Staging
**Objective**: Deploy to staging environment

**Tasks**:
1. Deploy chat function to staging
2. Configure staging environment variables
3. Test in staging environment
4. Monitor logs and errors
5. Gather feedback

**Test Criteria**:
- ✅ Function deploys successfully
- ✅ Endpoints work in staging
- ✅ No critical errors
- ✅ Performance is acceptable

**Test Command**:
```bash
sam deploy --config-env staging
```

**Rollback**: Revert deployment

---

### Step 9.2: Set Up Monitoring
**Objective**: Monitor chatbot performance and costs

**Tasks**:
1. Set up CloudWatch dashboards
2. Create alarms for errors
3. Monitor embedding costs
4. Track response times
5. Monitor Gemini Live API usage and costs
6. Monitor user satisfaction

**Test Criteria**:
- ✅ Dashboards are created
- ✅ Alarms are configured
- ✅ Cost monitoring works
- ✅ Performance metrics are tracked

**Files to Create**:
- CloudWatch dashboard configuration (JSON)
- GCP Monitoring dashboard (for Gemini Live API)

**Rollback**: Remove monitoring

---

### Step 9.3: Implement Conversation Logging and Admin Access
**Objective**: Enable administrators to review user questions and chatbot responses with summaries

**Tasks**:
1. **Create Conversation History Storage**
   - Create DynamoDB table for conversation logs
   - Store: user_id, session_id, timestamp, question, response, summary, metadata
   - Implement TTL for data retention (e.g., 90 days)
   - Index by user_id and timestamp for efficient queries
   - Index by session_id for session-based queries

2. **Implement Conversation Logging**
   - Log every user question and chatbot response
   - Include metadata: timestamp, session_id, connection_id, message_type (text/voice)
   - Store RAG context used (for debugging)
   - Store tool calls made (for analysis)
   - Generate summary of each conversation turn (using Gemini API)
   - Handle PII/sensitive data appropriately

3. **Create Conversation Summary Service**
   - Generate summary for each user inquiry using Gemini API
   - Include: question category, key topics, response type
   - Store summary with conversation log
   - Batch summarize multiple turns if needed

4. **Create Admin Endpoints**
   - `GET /api/v1/admin/chat/conversations` - List all conversations with summaries
   - `GET /api/v1/admin/chat/conversations/{session_id}` - Get specific conversation
   - `GET /api/v1/admin/chat/conversations/user/{user_id}` - Get user's conversations
   - `GET /api/v1/admin/chat/summaries` - Get conversation summaries only
   - `GET /api/v1/admin/chat/stats` - Get conversation statistics
   - Add admin authentication/authorization (Cognito admin role)

5. **Implement CloudWatch Logs**
   - Log conversations to CloudWatch Logs
   - Include structured JSON logs for easy querying
   - Set up log retention (14-30 days)
   - Enable log filtering by user_id, session_id, etc.

6. **Add Privacy Controls**
   - Option to disable logging per user (if required by privacy policy)
   - Option to anonymize user_id in logs
   - Clear data retention policy
   - GDPR/privacy compliance considerations

**Test Criteria**:
- ✅ Conversations are logged to DynamoDB
- ✅ Conversation summaries are generated and stored
- ✅ Conversations are logged to CloudWatch
- ✅ Admin endpoints return conversation history with summaries
- ✅ Admin authentication works
- ✅ Data retention (TTL) works correctly
- ✅ Privacy controls work

**Files to Create**:
- `app/api/v1/chat/services/conversation_logger.py`
- `app/api/v1/chat/services/conversation_summarizer.py`
- `app/api/v1/admin/endpoints/chat_conversations.py`
- `app/api/v1/admin/schemas/conversation.py`

**Files to Modify**:
- `app/api/v1/chat/app.py` (add logging calls in $default handler)
- `template.yaml` (add ConversationLogsTable and AdminFunction)

**DynamoDB Table Schema**:
```yaml
ConversationLogsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub "${AWS::StackName}-chat-conversations"
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: sessionId
        AttributeType: S
      - AttributeName: timestamp
        AttributeType: S
      - AttributeName: userId
        AttributeType: S
    KeySchema:
      - AttributeName: sessionId
        KeyType: HASH
      - AttributeName: timestamp
        KeyType: RANGE
    GlobalSecondaryIndexes:
      - IndexName: userId-timestamp-index
        KeySchema:
          - AttributeName: userId
            KeyType: HASH
          - AttributeName: timestamp
            KeyType: RANGE
        Projection:
          ProjectionType: ALL
    TimeToLiveSpecification:
      AttributeName: ttl
      Enabled: true
    Tags:
      - Key: Environment
        Value: !Sub "${AWS::StackName}"
```

**Conversation Logger Implementation**:
```python
# app/api/v1/chat/services/conversation_logger.py
import boto3
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import logging
from .conversation_summarizer import ConversationSummarizer

logger = logging.getLogger(__name__)

class ConversationLogger:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.getenv('CONVERSATION_LOGS_TABLE_NAME'))
        self.logs_client = boto3.client('logs')
        self.log_group = os.getenv('CONVERSATION_LOG_GROUP', '/aws/lambda/chat-conversations')
        self.summarizer = ConversationSummarizer()
        
    def log_conversation(
        self,
        user_id: str,
        session_id: str,
        question: str,
        response: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ):
        """Log conversation to DynamoDB and CloudWatch with summary"""
        timestamp = datetime.now(timezone.utc).isoformat()
        ttl = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
        
        # Generate summary
        summary = self.summarizer.summarize(question, response)
        
        item = {
            'sessionId': session_id,
            'timestamp': timestamp,
            'userId': user_id,
            'question': question,
            'response': response,
            'summary': summary,  # Generated summary
            'messageType': message_type,
            'metadata': metadata or {},
            'ttl': ttl
        }
        
        # Store in DynamoDB
        try:
            self.table.put_item(Item=item)
        except Exception as e:
            logger.error(f"Error logging conversation to DynamoDB: {str(e)}")
        
        # Also log to CloudWatch
        try:
            log_event = {
                'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
                'message': json.dumps({
                    'sessionId': session_id,
                    'userId': user_id,
                    'question': question,
                    'response': response,
                    'summary': summary,
                    'messageType': message_type,
                    'metadata': metadata
                })
            }
            self.logs_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=session_id,
                logEvents=[log_event]
            )
        except Exception as e:
            logger.error(f"Error logging conversation to CloudWatch: {str(e)}")
```

**Conversation Summarizer Implementation**:
```python
# app/api/v1/chat/services/conversation_summarizer.py
import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

class ConversationSummarizer:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def summarize(self, question: str, response: str) -> Dict[str, str]:
        """
        Generate summary of conversation turn
        
        Returns:
            {
                'category': 'word_meaning' | 'grammar' | 'progress' | 'general',
                'topics': ['word', 'meaning', 'usage'],
                'response_type': 'explanation' | 'tool_call' | 'recommendation',
                'key_points': 'Brief summary of what was discussed'
            }
        """
        prompt = f"""Analyze this conversation turn and provide a structured summary:

User Question: {question}
Chatbot Response: {response[:500]}...

Provide a JSON summary with:
1. category: One of ['word_meaning', 'grammar', 'progress', 'kanji', 'sentence', 'general']
2. topics: List of 2-5 key topics discussed
3. response_type: One of ['explanation', 'tool_call', 'recommendation', 'question']
4. key_points: Brief 1-2 sentence summary of what was discussed

Return only valid JSON, no markdown.
"""
        
        try:
            result = self.model.generate_content(prompt)
            summary_text = result.text.strip()
            # Remove markdown code blocks if present
            if summary_text.startswith('```'):
                summary_text = summary_text.split('```')[1]
                if summary_text.startswith('json'):
                    summary_text = summary_text[4:]
                summary_text = summary_text.strip()
            
            import json
            summary = json.loads(summary_text)
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback summary
            return {
                'category': 'general',
                'topics': [],
                'response_type': 'explanation',
                'key_points': 'Conversation logged'
            }
```

**Admin Endpoint Example**:
```python
# app/api/v1/admin/endpoints/chat_conversations.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from services.conversation_logger import ConversationLogger
from common.auth import require_admin_role  # Admin authentication
from schemas.conversation import ConversationResponse, ConversationSummary

router = APIRouter()
conversation_logger = ConversationLogger()

@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    limit: int = Query(100, ge=1, le=1000),
    start_key: Optional[str] = None,
    admin_user = Depends(require_admin_role)
):
    """
    List all conversations with summaries (admin only)
    Returns basic info and summary of each user inquiry
    """
    # Query DynamoDB for conversations
    # Return paginated results with summaries
    pass

@router.get("/conversations/user/{user_id}", response_model=List[ConversationSummary])
async def get_user_conversations(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    admin_user = Depends(require_admin_role)
):
    """
    Get conversations for a specific user with summaries (admin only)
    """
    # Query by userId using GSI
    pass

@router.get("/conversations/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    session_id: str,
    admin_user = Depends(require_admin_role)
):
    """
    Get specific conversation by session ID with full details (admin only)
    """
    # Query by sessionId
    pass

@router.get("/summaries", response_model=List[ConversationSummary])
async def get_conversation_summaries(
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    admin_user = Depends(require_admin_role)
):
    """
    Get conversation summaries only (admin only)
    Useful for quick overview of user inquiries
    """
    # Query conversations and return only summaries
    pass
```

**Schema Example**:
```python
# app/api/v1/admin/schemas/conversation.py
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class ConversationSummary(BaseModel):
    """Summary view for admin - basic info and summary"""
    sessionId: str
    timestamp: str
    userId: str
    question: str
    summary: Dict[str, str]  # category, topics, response_type, key_points
    messageType: str

class ConversationResponse(BaseModel):
    """Full conversation details"""
    sessionId: str
    timestamp: str
    userId: str
    question: str
    response: str
    summary: Dict[str, str]
    messageType: str
    metadata: Optional[Dict] = None
```

**Test Method**:
1. Send a message via chatbot
2. Verify conversation logged in DynamoDB with summary
3. Verify conversation logged in CloudWatch
4. Call admin endpoint to retrieve conversation summaries
5. Verify summaries contain category, topics, key_points
6. Verify admin authentication works
7. Test filtering by category or user_id
8. Test TTL expiration (after retention period)

**Privacy Considerations**:
- **Data Retention**: 90 days TTL (configurable)
- **User Consent**: Consider adding user consent for logging
- **PII Handling**: Option to redact sensitive information
- **Access Control**: Strict admin-only access via Cognito
- **Compliance**: Ensure GDPR/privacy law compliance

**Cost Impact**:
- DynamoDB: ~$0.25 per million writes (minimal for conversation logs)
- CloudWatch Logs: First 5GB free, then $0.50/GB
- Gemini API for summaries: ~$0.10 per 1K summaries
- **Estimated**: < $0.20/month for moderate usage

**Rollback**: Disable conversation logging, remove admin endpoints

---

### Step 9.4: Production Deployment
**Objective**: Deploy to production

**Tasks**:
1. Deploy chat function to production
2. Configure production environment
3. Test production endpoints
4. Monitor initial usage
5. Gather user feedback

**Test Criteria**:
- ✅ Production deployment successful
- ✅ Production endpoints work
- ✅ No critical issues
- ✅ Users can access chatbot

**Test Command**:
```bash
sam deploy --config-env prod
```

**Rollback**: Revert to previous version

---

## Implementation Checklist

### Phase 1: Infrastructure
- [ ] Set up Gemini 2.5 Flash Live API (Vertex AI)
- [ ] Enable AWS Bedrock access (for embeddings)
- [ ] Add dependencies to requirements.txt
- [ ] Configure IAM permissions (AWS)
- [ ] Configure GCP authentication (Vertex AI)

### Phase 2: Embeddings
- [ ] Create embedding generation script
- [ ] Generate embeddings for existing data
- [ ] Create embedding update hook

### Phase 3: FAISS Index
- [ ] Create FAISS index builder
- [ ] Implement index loading in Lambda
- [ ] Test index save/load

### Phase 4: LangChain
- [ ] Set up Bedrock embeddings
- [ ] Create FAISS vector store
- [ ] Build RAG chain

### Phase 5: Tools
- [ ] Create DynamoDB tool functions (words, kanjis, sentences)
- [ ] Create user progress & plan tool functions
- [ ] Integrate tools with Gemini Live API (Function Calling)
- [ ] Test tool calling

### Phase 6: Gemini Live API Integration
- [ ] Integrate Gemini Live API with RAG
- [ ] Set up WebSocket handler (WSS)
- [ ] Configure RAG context injection
- [ ] Inject user context at session start
- [ ] Test text and voice modes
- [ ] Add to SAM template

### Phase 7: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Performance testing
- [ ] Cost validation

### Phase 8: Quality
- [ ] Response quality testing
- [ ] Prompt engineering
- [ ] Error handling

### Phase 9: Deployment
- [ ] Deploy to staging
- [ ] Set up monitoring
- [ ] Implement conversation logging and admin access
- [ ] Deploy to production

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Infrastructure | 1-2 days | None |
| Phase 2: Embeddings | 2-3 days | Phase 1 |
| Phase 3: FAISS Index | 2 days | Phase 2 |
| Phase 4: LangChain | 2-3 days | Phase 3 |
| Phase 5: Tools | 2 days | Phase 4 |
| Phase 6: Gemini Live API Integration | 2-3 days | Phase 5 |
| Phase 7: Testing | 2-3 days | Phase 6 |
| Phase 8: Quality | 2-3 days | Phase 7 |
| Phase 9: Deployment | 2-3 days | Phase 8 |

**Total**: 17-24 days (3.5-5 weeks)

**Note**: Phase 9 includes conversation logging and admin access (Step 9.3)

---

## Success Criteria

### Functional
- ✅ Chatbot answers questions accurately (> 90%)
- ✅ Retrieves relevant context from database
- ✅ Uses tool calling when appropriate
- ✅ Maintains conversation context
- ✅ Handles errors gracefully
- ✅ Supports both text and voice input/output
- ✅ Real-time voice conversation works smoothly

### Performance
- ✅ Cold start < 5 seconds
- ✅ Warm invocation < 2 seconds
- ✅ Response time < 3 seconds
- ✅ Voice response latency < 1 second (first audio chunk)
- ✅ Can handle 100+ concurrent users

### Cost

**Base RAG Infrastructure (Phase 1-5)**:
- ✅ Embedding costs: < $1/month
- ✅ DynamoDB: < $0.50/month (within free tier)
- ✅ S3 (FAISS index): < $0.10/month
- ✅ Lambda: < $0.50/month
- **Total Base**: < $2/month ✅

**Gemini 2.5 Flash Live API Usage**:

**Pricing** (as of 2024):
- **Audio Input**: $3.00 per million tokens (25 tokens/second)
- **Audio Output**: $12.00 per million tokens (25 tokens/second)
- **Text Input**: $0.50 per million tokens
- **Text Output**: $2.00 per million tokens

**Cost Examples**:

**5-minute voice session**:
- User speech: 300 seconds × 25 tokens/sec = 7,500 tokens
- AI response: 150 seconds × 25 tokens/sec = 3,750 tokens
- Input cost: (7,500 / 1M) × $3.00 = **$0.0225**
- Output cost: (3,750 / 1M) × $12.00 = **$0.045**
- **Total per session**: **$0.0675**

**Monthly Cost Scenarios**:
- **Low usage** (30 sessions/month): ~$2.03/month ✅
- **Moderate usage** (50 sessions/month): ~$3.38/month
- **High usage** (100 sessions/month): ~$6.75/month

**Text-only sessions** (much cheaper):
- 1,000 text messages: ~$0.25-0.50/month

**Recommendation**: 
- For < $2/month total: Limit to ~30 voice sessions/month
- Or use text mode for most interactions (much cheaper)
- Voice for premium features only

### Quality
- ✅ No significant hallucinations
- ✅ Responses are helpful and accurate
- ✅ User satisfaction > 80%
- ✅ Voice responses are natural and clear

---

## Risk Mitigation

### Risk 1: Bedrock Access Delayed
**Mitigation**: Use self-hosted embeddings as fallback

### Risk 2: Lambda Package Too Large
**Mitigation**: Optimize dependencies, use Lambda layers

### Risk 3: Cold Start Too Slow
**Mitigation**: Use provisioned concurrency, optimize index loading

### Risk 4: Costs Exceed Budget
**Mitigation**: Monitor costs closely, implement caching, optimize queries

### Risk 5: Response Quality Poor
**Mitigation**: Iterative prompt engineering, better retrieval, more context

### Risk 6: Gemini Live API Access/Availability
**Mitigation**: 
- Check Vertex AI access in GCP Console
- Enable Vertex AI API
- Verify Gemini 2.5 Flash Live API is available in your region
- Have fallback to regular Gemini API if needed

### Risk 7: Gemini Live API Costs Too High
**Mitigation**: 
- Monitor usage closely (Cloud Monitoring)
- Implement rate limiting
- Use text mode for most interactions (10x cheaper)
- Cache common responses
- Use voice only for premium features
- Set budget alerts in GCP

### Risk 8: Audio Quality or Latency Issues
**Mitigation**: 
- Test with different audio formats (PCM 16kHz input, 24kHz output)
- Optimize WebSocket connection
- Use appropriate audio codecs
- Test in different network conditions

---

## Next Steps

1. **Review this plan** - using Gemini 2.5 Flash Live API from start
2. **Enable Vertex AI**: Set up Gemini Live API in GCP Console
3. **Start Phase 1**: Set up Gemini Live API access
4. **Complete Phase 1-9**: Deploy with text + voice from Phase 6
5. **Monitor costs**: Track usage to stay within budget

**Key Advantage**: Gemini Live API handles everything - text, voice, VAD, turn-taking, interrupts - from the start! 🚀
