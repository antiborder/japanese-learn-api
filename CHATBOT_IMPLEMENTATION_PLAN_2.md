# AI Chatbot Implementation Plan 2 - Phased Approach

## Overview

Implement an AI chatbot in phases, starting simple and gradually adding features:
1. **Phase 1**: Simple text chat (REST API, no DB/vectorization)
2. **Phase 2**: Text chat with conversation logging (admin view)
3. **Phase 3**: Full chat with RAG, DB, and tool calling
4. **Phase 4**: Real-time text chat (WebSocket) - *Timing TBD*
5. **Phase 5**: Real-time voice chat (WebSocket) - *Timing TBD*

**Budget**: 
- Phase 1-2: < $1/month (Gemini API only)
- Phase 3: < $2/month (RAG infrastructure)
- Phase 4-5: +$1-4/month (Gemini Live API usage)
- **Total**: ~$2-6/month depending on features and usage

**Timeline**: 20-30 days (4-6 weeks) - phased approach allows incremental deployment

---

## Development Strategy: Incremental Phases

### **Why This Approach**

✅ **Lower Risk**: Each phase is independently deployable and testable
✅ **Faster Initial Delivery**: Phase 1 can be deployed quickly
✅ **Easier Debugging**: Simpler phases make issues easier to isolate
✅ **User Feedback**: Get feedback early, iterate based on needs
✅ **Cost Control**: Only pay for features you're using

### **Phase Dependencies**

```
Phase 1 (Simple Text Chat)
    ↓
Phase 2 (Text Chat + Logging)
    ↓
Phase 3 (Full RAG Chat)
    ↓
Phase 4 (WebSocket Real-time Text) ← Optional, can skip to Phase 5
    ↓
Phase 5 (WebSocket Real-time Voice)
```

---

## Phase 1: Simple Text Chat (REST API)

**Objective**: Get basic chatbot working with Gemini 2.5 Flash Live API via REST API

**Scope**:
- ✅ REST API endpoint for text chat
- ✅ Direct integration with Gemini API (no Live API yet)
- ✅ Simple request/response
- ✅ No database access
- ✅ No vectorization
- ✅ No RAG
- ✅ No tool calling

**Why Start Here**:
- Simplest possible implementation
- Fastest to deploy and test
- Validates Gemini API integration
- Foundation for all future phases

**Timeline**: 2-3 days

---

### Step 1.1: Set Up Gemini API Access
**Objective**: Configure basic Gemini API access

**Tasks**:
1. Get Gemini API key (or use existing)
2. Set up API key in AWS Secrets Manager
3. Test basic API connection
4. Verify API quota and limits

**Test Criteria**:
- ✅ API key is configured
- ✅ Can make test API call
- ✅ Response is received

**Files to Create**:
- `app/api/v1/chat/integrations/gemini_client.py`

**Implementation**:
```python
# app/api/v1/chat/integrations/gemini_client.py
import google.generativeai as genai
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        api_key = self._get_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def _get_api_key(self) -> str:
        """Get Gemini API key from Secrets Manager or environment"""
        # Try Secrets Manager first
        try:
            import boto3
            secrets_client = boto3.client('secretsmanager')
            secret = secrets_client.get_secret_value(
                SecretId=os.getenv('GEMINI_API_KEY_SECRET_NAME', 'gemini-api-key')
            )
            return secret['SecretString']
        except Exception as e:
            logger.warning(f"Could not get API key from Secrets Manager: {e}")
            # Fallback to environment variable
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment or Secrets Manager")
            return api_key
    
    def chat(self, message: str, conversation_history: Optional[list] = None) -> str:
        """
        Send message to Gemini API and get response
        
        Args:
            message: User's message
            conversation_history: Optional list of previous messages for context
        
        Returns:
            Chatbot response text
        """
        try:
            if conversation_history:
                # Build conversation context
                chat = self.model.start_chat(history=conversation_history)
                response = chat.send_message(message)
            else:
                # Simple one-shot request
                response = self.model.generate_content(message)
            
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
```

**Test Command**:
```python
from app.api.v1.chat.integrations.gemini_client import GeminiClient
client = GeminiClient()
response = client.chat("Hello, what is Japanese?")
assert len(response) > 0
```

---

### Step 1.2: Create REST API Endpoint
**Objective**: Create simple REST endpoint for text chat

**Tasks**:
1. Create FastAPI endpoint: `POST /api/v1/chat/message`
2. Accept text message in request body
3. Call Gemini API
4. Return response
5. Add basic error handling
6. Add user authentication (extract user_id from JWT token)

**Test Criteria**:
- ✅ Endpoint accepts POST requests
- ✅ Returns chatbot response
- ✅ Error handling works
- ✅ User authentication works

**Files to Create**:
- `app/api/v1/chat/endpoints/chat.py`
- `app/api/v1/chat/schemas/chat.py`
- `app/api/v1/chat/app.py`

**Schema Implementation**:
```python
# app/api/v1/chat/schemas/chat.py
from pydantic import BaseModel
from typing import Optional

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # For conversation continuity

class ChatMessageResponse(BaseModel):
    response: str
    session_id: str
```

**Endpoint Implementation**:
```python
# app/api/v1/chat/endpoints/chat.py
from fastapi import APIRouter, HTTPException, Depends
from schemas.chat import ChatMessageRequest, ChatMessageResponse
from integrations.gemini_client import GeminiClient
from common.auth import get_current_user_id  # Existing auth dependency
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Simple text chat endpoint
    No RAG, no DB access, just direct Gemini API call
    """
    try:
        client = GeminiClient()
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Call Gemini API
        response_text = client.chat(request.message)
        
        return ChatMessageResponse(
            response=response_text,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
```

**App Implementation**:
```python
# app/api/v1/chat/app.py
from fastapi import FastAPI
from mangum import Mangum
from endpoints.chat import router as chat_router
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Japanese Learn API - Chat", version="1.0.0")

# Include routers
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

# Mangum handler for Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """Lambda handler for FastAPI app"""
    try:
        stage = event.get('requestContext', {}).get('stage', '')
        if stage:
            app.root_path = f"/{stage}"
        response = handler(event, context)
        
        # Add CORS headers
        if 'headers' not in response:
            response['headers'] = {}
        response['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        })
        
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': '{"error": "Internal server error"}',
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
```

**Test Command**:
```bash
curl -X POST https://api.example.com/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "Hello"}'
```

---

### Step 1.3: Add to SAM Template
**Objective**: Deploy simple chat function

**Tasks**:
1. Add ChatFunction to template.yaml
2. Configure REST API Gateway
3. Set environment variables (Gemini API key secret name)
4. Configure IAM permissions (Secrets Manager, DynamoDB for auth)

**Test Criteria**:
- ✅ Function deploys successfully
- ✅ REST API endpoint works
- ✅ Can send/receive messages
- ✅ Authentication works

**Files to Modify**:
- `template.yaml`

**SAM Template Configuration**:
```yaml
# Add to template.yaml

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
    Description: "Lambda function for simple AI chatbot (Phase 1)"
    Runtime: python3.11
    MemorySize: 256
    Timeout: 30
    Environment:
      Variables:
        GEMINI_API_KEY_SECRET_NAME: !Sub "${AWS::StackName}-gemini-api-key"
        LOG_LEVEL: INFO
    Events:
      ChatApiRootEvent:
        Type: Api
        Properties:
          Path: /api/v1/chat
          Method: ANY
      ChatApiProxyEvent:
        Type: Api
        Properties:
          Path: /api/v1/chat/{proxy+}
          Method: ANY
    Policies:
      - Statement:
        - Effect: Allow
          Action:
            - secretsmanager:GetSecretValue
          Resource:
            - !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:${AWS::StackName}-gemini-api-key*"
        # DynamoDB read for user authentication (if using existing auth)
        - Effect: Allow
          Action:
            - dynamodb:GetItem
            - dynamodb:Query
          Resource:
            - !Sub "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}"
            - !Sub "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*"

# Gemini API Key Secret (if not already exists)
GeminiApiKeySecret:
  Type: AWS::SecretsManager::Secret
  Properties:
    Name: !Sub "${AWS::StackName}-gemini-api-key"
    Description: "Gemini API Key for chatbot"
    SecretString: !Ref GeminiApiKey  # Parameter from existing template
```

**Dependencies to Add** (Phase 1 only):
```txt
# app/api/v1/chat/requirements.txt
google-generativeai>=0.3.0
boto3>=1.28.0
fastapi>=0.104.0
mangum>=0.17.0
pydantic>=2.0.0
```

**Test Command**:
```bash
sam build
sam deploy --guided
```

---

## Phase 2: Text Chat with Conversation Logging

**Objective**: Add conversation logging and admin access to view user inquiries

**Scope**:
- ✅ Keep REST API text chat (from Phase 1)
- ✅ Add conversation logging to DynamoDB
- ✅ Generate summaries using Gemini API
- ✅ Create admin endpoints to view conversations
- ✅ Still no DB/vectorization for chat responses

**Why This Phase**:
- Adds valuable admin visibility
- Validates logging infrastructure
- Prepares for future phases
- Can be deployed independently

**Timeline**: 2-3 days

---

### Step 2.1: Create Conversation Logging
**Objective**: Log all user questions and chatbot responses

**Tasks**:
1. Create DynamoDB table for conversation logs
2. Create conversation logger service
3. Integrate logging into chat endpoint
4. Store: user_id, session_id, question, response, timestamp, message_type
5. Implement TTL for data retention (90 days)

**Test Criteria**:
- ✅ Conversations are logged to DynamoDB
- ✅ Logs include all required fields
- ✅ Logging doesn't break chat functionality
- ✅ TTL is set correctly

**Files to Create**:
- `app/api/v1/chat/services/conversation_logger.py`

**Files to Modify**:
- `app/api/v1/chat/endpoints/chat.py` (add logging call)
- `template.yaml` (add ConversationLogsTable)

**Conversation Logger Implementation**:
```python
# app/api/v1/chat/services/conversation_logger.py
import boto3
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ConversationLogger:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.getenv('CONVERSATION_LOGS_TABLE_NAME'))
    
    def log_conversation(
        self,
        user_id: str,
        session_id: str,
        question: str,
        response: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ):
        """
        Log conversation to DynamoDB
        
        Args:
            user_id: User ID from authentication
            session_id: Session ID for conversation continuity
            question: User's question
            response: Chatbot's response
            message_type: "text" or "voice"
            metadata: Optional additional metadata
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            ttl = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
            
            item = {
                'sessionId': session_id,
                'timestamp': timestamp,
                'userId': user_id,
                'question': question,
                'response': response,
                'messageType': message_type,
                'metadata': metadata or {},
                'ttl': ttl
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Logged conversation for user {user_id}, session {session_id}")
        except Exception as e:
            logger.error(f"Error logging conversation: {str(e)}")
            # Don't fail the request if logging fails
```

**DynamoDB Table Schema**:
```yaml
# Add to template.yaml
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

**Update Chat Endpoint**:
```python
# Modify app/api/v1/chat/endpoints/chat.py
from services.conversation_logger import ConversationLogger

conversation_logger = ConversationLogger()

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Simple text chat with logging"""
    try:
        client = GeminiClient()
        session_id = request.session_id or str(uuid.uuid4())
        
        # Call Gemini API
        response_text = client.chat(request.message)
        
        # Log conversation (async, non-blocking)
        try:
            conversation_logger.log_conversation(
                user_id=user_id,
                session_id=session_id,
                question=request.message,
                response=response_text,
                message_type="text"
            )
        except Exception as e:
            logger.warning(f"Failed to log conversation: {e}")
            # Continue even if logging fails
        
        return ChatMessageResponse(
            response=response_text,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
```

**Update template.yaml**:
```yaml
# Add to ChatFunction Environment Variables
Environment:
  Variables:
    GEMINI_API_KEY_SECRET_NAME: !Sub "${AWS::StackName}-gemini-api-key"
    CONVERSATION_LOGS_TABLE_NAME: !Ref ConversationLogsTable
    LOG_LEVEL: INFO

# Add DynamoDB write permission for conversation logs
Policies:
  - Statement:
    # ... existing statements ...
    - Effect: Allow
      Action:
        - dynamodb:PutItem
        - dynamodb:Query
      Resource:
        - !GetAtt ConversationLogsTable.Arn
        - !Sub "${ConversationLogsTable.Arn}/index/*"
```

---

### Step 2.2: Create Conversation Summarizer
**Objective**: Generate summaries of each conversation turn

**Tasks**:
1. Create summarizer service using Gemini API
2. Generate structured summary (category, topics, key_points, response_type)
3. Store summary with conversation log
4. Handle errors gracefully (fallback summary)
5. Optimize for cost (use Gemini 2.0 Flash Exp for summaries)

**Test Criteria**:
- ✅ Summaries are generated for each conversation
- ✅ Summaries contain category, topics, key_points, response_type
- ✅ Error handling works (fallback summary)
- ✅ Summary generation doesn't slow down chat response

**Files to Create**:
- `app/api/v1/chat/services/conversation_summarizer.py`

**Files to Modify**:
- `app/api/v1/chat/services/conversation_logger.py` (integrate summarizer)

**Conversation Summarizer Implementation**:
```python
# app/api/v1/chat/services/conversation_summarizer.py
import google.generativeai as genai
import os
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ConversationSummarizer:
    def __init__(self):
        api_key = self._get_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def _get_api_key(self) -> str:
        """Get Gemini API key (same as GeminiClient)"""
        try:
            import boto3
            secrets_client = boto3.client('secretsmanager')
            secret = secrets_client.get_secret_value(
                SecretId=os.getenv('GEMINI_API_KEY_SECRET_NAME', 'gemini-api-key')
            )
            return secret['SecretString']
        except Exception as e:
            logger.warning(f"Could not get API key from Secrets Manager: {e}")
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found")
            return api_key
    
    def summarize(self, question: str, response: str) -> Dict[str, any]:
        """
        Generate summary of conversation turn
        
        Returns:
            {
                'category': 'word_meaning' | 'grammar' | 'progress' | 'kanji' | 'sentence' | 'general',
                'topics': ['word', 'meaning', 'usage'],
                'response_type': 'explanation' | 'tool_call' | 'recommendation' | 'question',
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

**Update Conversation Logger**:
```python
# Modify app/api/v1/chat/services/conversation_logger.py
from .conversation_summarizer import ConversationSummarizer

class ConversationLogger:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.getenv('CONVERSATION_LOGS_TABLE_NAME'))
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
        """Log conversation with summary"""
        try:
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
                'summary': summary,  # Add summary
                'messageType': message_type,
                'metadata': metadata or {},
                'ttl': ttl
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Logged conversation with summary for user {user_id}")
        except Exception as e:
            logger.error(f"Error logging conversation: {str(e)}")
```

---

### Step 2.3: Create Admin Endpoints
**Objective**: Enable admins to view conversation history and summaries

**Tasks**:
1. Create admin endpoints:
   - `GET /api/v1/admin/chat/conversations` - List all with summaries
   - `GET /api/v1/admin/chat/conversations/user/{user_id}` - User's conversations
   - `GET /api/v1/admin/chat/conversations/{session_id}` - Specific conversation
   - `GET /api/v1/admin/chat/summaries` - Summaries only
   - `GET /api/v1/admin/chat/stats` - Conversation statistics
2. Add admin authentication (Cognito admin role)
3. Implement pagination
4. Add filtering by category, date, user

**Test Criteria**:
- ✅ Admin endpoints return conversation data
- ✅ Summaries are included in responses
- ✅ Admin authentication works
- ✅ Pagination works
- ✅ Filtering works

**Files to Create**:
- `app/api/v1/admin/endpoints/chat_conversations.py`
- `app/api/v1/admin/schemas/conversation.py`
- `app/api/v1/admin/app.py`

**Schema Implementation**:
```python
# app/api/v1/admin/schemas/conversation.py
from pydantic import BaseModel
from typing import Optional, Dict, List

class ConversationSummary(BaseModel):
    """Summary view for admin - basic info and summary"""
    sessionId: str
    timestamp: str
    userId: str
    question: str
    summary: Dict[str, any]  # category, topics, response_type, key_points
    messageType: str

class ConversationResponse(BaseModel):
    """Full conversation details"""
    sessionId: str
    timestamp: str
    userId: str
    question: str
    response: str
    summary: Dict[str, any]
    messageType: str
    metadata: Optional[Dict] = None

class ConversationStats(BaseModel):
    """Conversation statistics"""
    total_conversations: int
    conversations_by_category: Dict[str, int]
    conversations_by_date: Dict[str, int]
    top_topics: List[Dict[str, int]]
```

**Admin Endpoint Implementation**:
```python
# app/api/v1/admin/endpoints/chat_conversations.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import boto3
import os
from schemas.conversation import ConversationSummary, ConversationResponse, ConversationStats
from common.auth import require_admin_role  # Admin authentication dependency
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

dynamodb = boto3.resource('dynamodb')
conversations_table = dynamodb.Table(os.getenv('CONVERSATION_LOGS_TABLE_NAME'))

@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    limit: int = Query(100, ge=1, le=1000),
    start_key: Optional[str] = None,
    category: Optional[str] = None,
    admin_user = Depends(require_admin_role)
):
    """
    List all conversations with summaries (admin only)
    Returns basic info and summary of each user inquiry
    """
    try:
        # Scan table with pagination
        scan_kwargs = {
            'Limit': limit
        }
        
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = json.loads(start_key)
        
        response = conversations_table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        # Filter by category if provided
        if category:
            items = [item for item in items 
                    if item.get('summary', {}).get('category') == category]
        
        # Convert to response models
        conversations = []
        for item in items:
            conversations.append(ConversationSummary(
                sessionId=item['sessionId'],
                timestamp=item['timestamp'],
                userId=item['userId'],
                question=item['question'],
                summary=item.get('summary', {}),
                messageType=item.get('messageType', 'text')
            ))
        
        return conversations
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/user/{user_id}", response_model=List[ConversationSummary])
async def get_user_conversations(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    admin_user = Depends(require_admin_role)
):
    """Get conversations for a specific user with summaries (admin only)"""
    try:
        # Query by userId using GSI
        response = conversations_table.query(
            IndexName='userId-timestamp-index',
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={
                ':userId': user_id
            },
            Limit=limit,
            ScanIndexForward=False  # Most recent first
        )
        
        items = response.get('Items', [])
        conversations = []
        for item in items:
            conversations.append(ConversationSummary(
                sessionId=item['sessionId'],
                timestamp=item['timestamp'],
                userId=item['userId'],
                question=item['question'],
                summary=item.get('summary', {}),
                messageType=item.get('messageType', 'text')
            ))
        
        return conversations
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    session_id: str,
    admin_user = Depends(require_admin_role)
):
    """Get specific conversation by session ID with full details (admin only)"""
    try:
        # Query by sessionId (get all messages in session)
        response = conversations_table.query(
            KeyConditionExpression='sessionId = :sessionId',
            ExpressionAttributeValues={
                ':sessionId': session_id
            }
        )
        
        items = response.get('Items', [])
        if not items:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Return most recent message (or aggregate all messages)
        item = sorted(items, key=lambda x: x['timestamp'], reverse=True)[0]
        
        return ConversationResponse(
            sessionId=item['sessionId'],
            timestamp=item['timestamp'],
            userId=item['userId'],
            question=item['question'],
            response=item['response'],
            summary=item.get('summary', {}),
            messageType=item.get('messageType', 'text'),
            metadata=item.get('metadata')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    try:
        # Similar to list_conversations but only return summaries
        scan_kwargs = {'Limit': limit}
        response = conversations_table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        if category:
            items = [item for item in items 
                    if item.get('summary', {}).get('category') == category]
        
        summaries = []
        for item in items:
            summaries.append(ConversationSummary(
                sessionId=item['sessionId'],
                timestamp=item['timestamp'],
                userId=item['userId'],
                question=item['question'],
                summary=item.get('summary', {}),
                messageType=item.get('messageType', 'text')
            ))
        
        return summaries
    except Exception as e:
        logger.error(f"Error getting summaries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=ConversationStats)
async def get_conversation_stats(
    admin_user = Depends(require_admin_role)
):
    """Get conversation statistics (admin only)"""
    try:
        # Scan all conversations (may be expensive, consider caching)
        response = conversations_table.scan()
        items = response.get('Items', [])
        
        # Calculate stats
        total = len(items)
        by_category = {}
        by_date = {}
        topics_count = {}
        
        for item in items:
            summary = item.get('summary', {})
            category = summary.get('category', 'general')
            by_category[category] = by_category.get(category, 0) + 1
            
            date = item['timestamp'][:10]  # YYYY-MM-DD
            by_date[date] = by_date.get(date, 0) + 1
            
            topics = summary.get('topics', [])
            for topic in topics:
                topics_count[topic] = topics_count.get(topic, 0) + 1
        
        top_topics = sorted(
            [{'topic': k, 'count': v} for k, v in topics_count.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        return ConversationStats(
            total_conversations=total,
            conversations_by_category=by_category,
            conversations_by_date=by_date,
            top_topics=top_topics
        )
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Admin App Implementation**:
```python
# app/api/v1/admin/app.py
from fastapi import FastAPI
from mangum import Mangum
from endpoints.chat_conversations import router as conversations_router
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Japanese Learn API - Admin", version="1.0.0")

app.include_router(conversations_router, prefix="/api/v1/admin/chat", tags=["admin", "chat"])

handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """Lambda handler for admin API"""
    try:
        stage = event.get('requestContext', {}).get('stage', '')
        if stage:
            app.root_path = f"/{stage}"
        response = handler(event, context)
        
        if 'headers' not in response:
            response['headers'] = {}
        response['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        })
        
        return response
    except Exception as e:
        logger.error(f"Error processing admin request: {str(e)}")
        return {
            'statusCode': 500,
            'body': '{"error": "Internal server error"}',
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
```

**Update template.yaml**:
```yaml
# Add AdminFunction
AdminFunction:
  Type: AWS::Serverless::Function
  Metadata:
    BuildMethod: python3.11
    BuildProperties:
      UseContainer: true
      ProjectPath: ./app/api/v1/admin
      InstallDependencies: true
  Properties:
    FunctionName: !Sub "${AWS::StackName}-AdminFunction"
    CodeUri: ./app/api/v1/admin
    Handler: app.lambda_handler
    Description: "Lambda function for admin endpoints"
    Runtime: python3.11
    MemorySize: 256
    Timeout: 30
    Environment:
      Variables:
        CONVERSATION_LOGS_TABLE_NAME: !Ref ConversationLogsTable
        LOG_LEVEL: INFO
    Events:
      AdminApiRootEvent:
        Type: Api
        Properties:
          Path: /api/v1/admin
          Method: ANY
      AdminApiProxyEvent:
        Type: Api
        Properties:
          Path: /api/v1/admin/{proxy+}
          Method: ANY
    Policies:
      - Statement:
        - Effect: Allow
          Action:
            - dynamodb:Query
            - dynamodb:Scan
            - dynamodb:GetItem
          Resource:
            - !GetAtt ConversationLogsTable.Arn
            - !Sub "${ConversationLogsTable.Arn}/index/*"
```

---

## Phase 3: Full RAG Chat with DB and Data Sources

**Objective**: Add RAG, vectorization, and tool calling for intelligent responses

**Scope**:
- ✅ Keep REST API text chat (from Phase 1-2)
- ✅ Add vector embeddings (Bedrock Titan)
- ✅ Add FAISS vector search
- ✅ Add LangChain RAG pipeline
- ✅ Add DynamoDB tool functions
- ✅ Add user progress/plan tool functions
- ✅ Integrate RAG context into Gemini API calls

**Why This Phase**:
- Adds intelligence to responses
- Enables access to app data
- Foundation for personalized responses
- Can still use REST API (no WebSocket yet)

**Timeline**: 8-12 days

---

### Step 3.1: Infrastructure Setup
**Objective**: Set up RAG infrastructure

**Tasks**:
1. Enable AWS Bedrock access (Titan embeddings)
2. Add LangChain, FAISS dependencies incrementally
3. Configure IAM permissions (Bedrock, S3, DynamoDB)
4. Set up S3 bucket for FAISS index storage
5. Configure S3 bucket in template.yaml

**Test Criteria**:
- ✅ Bedrock access enabled
- ✅ Dependencies installed
- ✅ Permissions configured
- ✅ S3 bucket created
- ✅ Can generate test embedding

**Files to Modify**:
- `app/api/v1/chat/requirements.txt` (add new dependencies)
- `template.yaml` (IAM policies, S3 bucket)

**Dependencies to Add** (Phase 3):
```txt
# app/api/v1/chat/requirements.txt
# Existing from Phase 1-2:
google-generativeai>=0.3.0
boto3>=1.28.0
fastapi>=0.104.0
mangum>=0.17.0
pydantic>=2.0.0

# New for Phase 3 (RAG):
langchain>=0.1.0
langchain-aws>=0.1.0
langchain-community>=0.0.20
faiss-cpu>=1.7.4  # CPU version for Lambda
numpy>=1.24.0  # Required by FAISS
```

**S3 Bucket Configuration**:
```yaml
# Add to template.yaml
S3BucketForFAISS:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub "${AWS::StackName}-faiss-index"
    VersioningConfiguration:
      Status: Enabled
    LifecycleConfiguration:
      Rules:
        - Id: DeleteOldVersions
          Status: Enabled
          NoncurrentVersionExpirationInDays: 7
    Tags:
      - Key: Environment
        Value: !Sub "${AWS::StackName}"
```

**IAM Permissions Update**:
```yaml
# Update ChatFunction Policies in template.yaml
ChatFunction:
  Properties:
    Policies:
      # ... existing policies from Phase 1-2 ...
      - Statement:
        # Bedrock for embeddings
        - Effect: Allow
          Action:
            - bedrock:InvokeModel
          Resource:
            - !Sub "arn:aws:bedrock:${AWS::Region}::foundation-model/amazon.titan-embed-text-v1"
        # S3 for FAISS index
        - Effect: Allow
          Action:
            - s3:GetObject
            - s3:PutObject
            - s3:ListBucket
          Resource:
            - !Sub "arn:aws:s3:::${S3BucketForFAISS}"
            - !Sub "arn:aws:s3:::${S3BucketForFAISS}/*"
        # DynamoDB for embeddings storage
        - Effect: Allow
          Action:
            - dynamodb:GetItem
            - dynamodb:PutItem
            - dynamodb:UpdateItem
            - dynamodb:Query
            - dynamodb:Scan
          Resource:
            - !Sub "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}"
            - !Sub "arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*"
```

**Environment Variables Update**:
```yaml
# Update ChatFunction Environment Variables
Environment:
  Variables:
    GEMINI_API_KEY_SECRET_NAME: !Sub "${AWS::StackName}-gemini-api-key"
    CONVERSATION_LOGS_TABLE_NAME: !Ref ConversationLogsTable
    DYNAMODB_TABLE_NAME: !Ref DynamoDBTable
    S3_BUCKET_NAME: !Ref S3BucketForFAISS
    FAISS_INDEX_S3_KEY: "faiss_index/index.faiss"
    FAISS_INDEX_METADATA_S3_KEY: "faiss_index/metadata.pkl"
    LOG_LEVEL: INFO
```

**Test Bedrock Access**:
```bash
# Test Bedrock access via AWS CLI
aws bedrock-runtime invoke-model \
  --model-id amazon.titan-embed-text-v1 \
  --body '{"inputText":"test"}' \
  --region us-east-1 \
  output.json

# Verify output
cat output.json | jq '.embedding | length'  # Should be 1536
```

**Lambda Memory/Timeout Update**:
```yaml
# Update ChatFunction for Phase 3 (needs more memory for FAISS)
ChatFunction:
  Properties:
    MemorySize: 1024  # Increased from 256 for FAISS index
    Timeout: 300  # Increased from 30 for embedding generation
```

---

### Step 3.2: Generate Embeddings
**Objective**: Vectorize existing data

**Tasks**:
1. Create embedding generation script
2. Generate embeddings for words, kanjis, sentences using Bedrock Titan
3. Store embeddings in DynamoDB as new attribute
4. Create embedding update hook for new/updated items
5. Support batch processing for efficiency

**Test Criteria**:
- ✅ Embeddings generated for all data
- ✅ Embeddings stored in DynamoDB (1536 dimensions)
- ✅ New data gets embeddings automatically
- ✅ Batch processing works correctly
- ✅ Error handling works for failed embeddings

**Files to Create**:
- `scripts/generate_embeddings.py`
- `app/api/v1/chat/services/embedding_service.py`

**Embedding Service Implementation**:
```python
# app/api/v1/chat/services/embedding_service.py
import boto3
import json
import os
import logging
from typing import List, Optional
from langchain_aws import BedrockEmbeddings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v1",
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of 1536 float values (embedding vector)
        """
        try:
            embedding = self.embeddings.embed_query(text)
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
            embeddings = self.embeddings.embed_documents(texts)
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
            if item.get('japanese'):
                parts.append(item['japanese'])
            if item.get('english'):
                parts.append(item['english'])
            # Add other languages if available
            for lang in ['vietnamese', 'chinese', 'korean']:
                if item.get(lang):
                    parts.append(item[lang])
            return ' '.join(parts)
        
        elif entity_type == 'kanji':
            parts = []
            if item.get('kanji'):
                parts.append(item['kanji'])
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
            embedding: Embedding vector
        """
        try:
            self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression='SET embedding = :embedding',
                ExpressionAttributeValues={
                    ':embedding': embedding
                }
            )
            logger.info(f"Stored embedding for {pk}/{sk}")
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            raise
```

**Embedding Generation Script**:
```python
# scripts/generate_embeddings.py
import boto3
import os
import argparse
import logging
from typing import List, Dict
from tqdm import tqdm
import sys

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
    table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME', 'japanese-learn-table'))
    
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
    
    # Process in batches
    batch_size = 25  # Bedrock batch limit
    failed = 0
    
    for i in tqdm(range(0, len(items_to_process), batch_size)):
        batch = items_to_process[i:i + batch_size]
        
        try:
            # Extract texts
            texts = [
                embedding_service.get_text_for_embedding(item, entity_type)
                for item in batch
            ]
            
            # Generate embeddings
            embeddings = embedding_service.generate_embeddings_batch(texts)
            
            # Store embeddings
            for item, embedding in zip(batch, embeddings):
                try:
                    embedding_service.store_embedding(
                        item['PK'],
                        item['SK'],
                        embedding
                    )
                except Exception as e:
                    logger.error(f"Failed to store embedding for {item['PK']}/{item['SK']}: {e}")
                    failed += 1
        
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            failed += len(batch)
    
    logger.info(f"Completed. Failed: {failed}/{len(items_to_process)}")

def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for DynamoDB items')
    parser.add_argument('--entity-type', choices=['word', 'kanji', 'sentence', 'all'],
                       default='all', help='Entity type to process')
    parser.add_argument('--limit', type=int, help='Limit number of items (for testing)')
    
    args = parser.parse_args()
    
    embedding_service = EmbeddingService()
    
    if args.entity_type == 'all':
        for entity_type in ['word', 'kanji', 'sentence']:
            logger.info(f"\n=== Processing {entity_type} ===")
            generate_embeddings_for_entity_type(embedding_service, entity_type, args.limit)
    else:
        generate_embeddings_for_entity_type(embedding_service, args.entity_type, args.limit)

if __name__ == '__main__':
    main()
```

**Embedding Update Hook**:
```python
# Modify existing endpoints to call embedding service
# Example: app/api/v1/words/endpoints/word.py

from app.api.v1.chat.services.embedding_service import EmbeddingService

embedding_service = EmbeddingService()

@router.post("/words", response_model=WordResponse)
async def create_word(word: WordCreate, user_id: str = Depends(get_current_user_id)):
    """Create word and generate embedding"""
    # ... existing word creation logic ...
    
    # Generate embedding asynchronously (don't block response)
    try:
        text = embedding_service.get_text_for_embedding(word_dict, 'word')
        embedding = embedding_service.generate_embedding(text)
        embedding_service.store_embedding('WORD', str(word_id), embedding)
    except Exception as e:
        logger.warning(f"Failed to generate embedding for word {word_id}: {e}")
        # Don't fail the request if embedding fails
    
    return word_response
```

**Test Commands**:
```bash
# Test with small subset
python scripts/generate_embeddings.py --limit 10 --entity-type word

# Generate for all words
python scripts/generate_embeddings.py --entity-type word

# Generate for all entity types
python scripts/generate_embeddings.py --entity-type all
```

---

### Step 3.3: Build FAISS Index
**Objective**: Create vector search index

**Tasks**:
1. Create FAISS index builder script
2. Build FAISS index from DynamoDB embeddings
3. Save index and metadata to S3
4. Implement index loading in Lambda (with caching)
5. Support incremental updates

**Test Criteria**:
- ✅ FAISS index created successfully
- ✅ Index contains all items with embeddings
- ✅ Index saved to S3
- ✅ Index loads in Lambda (< 2 seconds)
- ✅ Similarity search works correctly

**Files to Create**:
- `scripts/build_faiss_index.py`
- `app/api/v1/chat/integrations/vector_store.py`

**Vector Store Implementation**:
```python
# app/api/v1/chat/integrations/vector_store.py
import faiss
import pickle
import boto3
import os
import numpy as np
import logging
from typing import List, Dict, Optional
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_aws import BedrockEmbeddings

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    def __init__(self):
        self.embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v1",
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.vector_store: Optional[FAISS] = None
        self.s3_client = boto3.client('s3')
        self.s3_bucket = os.getenv('S3_BUCKET_NAME')
        self.index_key = os.getenv('FAISS_INDEX_S3_KEY', 'faiss_index/index.faiss')
        self.metadata_key = os.getenv('FAISS_INDEX_METADATA_S3_KEY', 'faiss_index/metadata.pkl')
    
    def build_index_from_dynamodb(self):
        """
        Build FAISS index from DynamoDB embeddings
        """
        import boto3
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))
        
        logger.info("Building FAISS index from DynamoDB...")
        
        # Collect all items with embeddings
        documents = []
        embeddings_list = []
        id_mapping = {}  # FAISS index -> (PK, SK, entity_type)
        
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
                
                response = table.query(**query_params)
                items = response.get('Items', [])
                
                for item in items:
                    embedding = item.get('embedding')
                    if embedding and len(embedding) == 1536:
                        # Create document
                        text = self._get_text_from_item(item, pk)
                        doc = Document(
                            page_content=text,
                            metadata={
                                'pk': item['PK'],
                                'sk': item['SK'],
                                'entity_type': pk.lower()
                            }
                        )
                        documents.append(doc)
                        embeddings_list.append(embedding)
                        
                        idx = len(embeddings_list) - 1
                        id_mapping[idx] = {
                            'pk': item['PK'],
                            'sk': item['SK'],
                            'entity_type': pk.lower()
                        }
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
        
        logger.info(f"Found {len(documents)} items with embeddings")
        
        if not documents:
            raise ValueError("No items with embeddings found")
        
        # Build FAISS index
        embeddings_array = np.array(embeddings_list, dtype=np.float32)
        
        # Create FAISS index (L2 distance)
        dimension = 1536
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings_array)
        
        # Create LangChain FAISS vector store
        self.vector_store = FAISS.from_embeddings(
            text_embeddings=list(zip([doc.page_content for doc in documents], embeddings_list)),
            embedding=self.embeddings,
            metadatas=[doc.metadata for doc in documents]
        )
        
        # Store ID mapping in metadata
        self.id_mapping = id_mapping
        
        logger.info(f"Built FAISS index with {index.ntotal} vectors")
        return self.vector_store
    
    def _get_text_from_item(self, item: dict, pk: str) -> str:
        """Extract text from DynamoDB item"""
        if pk == 'WORD':
            parts = [item.get('japanese', ''), item.get('english', '')]
            return ' '.join(filter(None, parts))
        elif pk == 'KANJI':
            parts = [item.get('kanji', ''), item.get('meaning', '')]
            return ' '.join(filter(None, parts))
        elif pk == 'SENTENCE':
            parts = [item.get('japanese', ''), item.get('english', '')]
            return ' '.join(filter(None, parts))
        return ""
    
    def save_to_s3(self):
        """Save FAISS index and metadata to S3"""
        if not self.vector_store:
            raise ValueError("No vector store to save")
        
        logger.info("Saving FAISS index to S3...")
        
        # Save FAISS index
        self.vector_store.save_local('/tmp/faiss_index')
        
        # Upload to S3
        self.s3_client.upload_file(
            '/tmp/faiss_index/index.faiss',
            self.s3_bucket,
            self.index_key
        )
        
        # Save and upload metadata
        metadata = {
            'id_mapping': self.id_mapping,
            'total_vectors': self.vector_store.index.ntotal
        }
        
        with open('/tmp/faiss_index/metadata.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        self.s3_client.upload_file(
            '/tmp/faiss_index/metadata.pkl',
            self.s3_bucket,
            self.metadata_key
        )
        
        logger.info("FAISS index saved to S3")
    
    def load_from_s3(self):
        """Load FAISS index from S3"""
        try:
            logger.info("Loading FAISS index from S3...")
            
            # Download from S3
            os.makedirs('/tmp/faiss_index', exist_ok=True)
            
            self.s3_client.download_file(
                self.s3_bucket,
                self.index_key,
                '/tmp/faiss_index/index.faiss'
            )
            
            self.s3_client.download_file(
                self.s3_bucket,
                self.metadata_key,
                '/tmp/faiss_index/metadata.pkl'
            )
            
            # Load FAISS index
            self.vector_store = FAISS.load_local(
                '/tmp/faiss_index',
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Load metadata
            with open('/tmp/faiss_index/metadata.pkl', 'rb') as f:
                metadata = pickle.load(f)
                self.id_mapping = metadata.get('id_mapping', {})
            
            logger.info(f"Loaded FAISS index with {self.vector_store.index.ntotal} vectors")
            return True
        
        except Exception as e:
            logger.error(f"Error loading FAISS index from S3: {e}")
            return False
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of similar documents
        """
        if not self.vector_store:
            raise ValueError("Vector store not loaded")
        
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """
        Search with similarity scores
        
        Returns:
            List of (Document, score) tuples
        """
        if not self.vector_store:
            raise ValueError("Vector store not loaded")
        
        return self.vector_store.similarity_search_with_score(query, k=k)
```

**FAISS Index Builder Script**:
```python
# scripts/build_faiss_index.py
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.api.v1.chat.integrations.vector_store import FAISSVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Building FAISS index...")
    
    vector_store = FAISSVectorStore()
    
    # Build index from DynamoDB
    vector_store.build_index_from_dynamodb()
    
    # Save to S3
    vector_store.save_to_s3()
    
    logger.info("FAISS index built and saved successfully")

if __name__ == '__main__':
    main()
```

**Test Commands**:
```bash
# Build index
python scripts/build_faiss_index.py

# Verify index
python -c "
from app.api.v1.chat.integrations.vector_store import FAISSVectorStore
vs = FAISSVectorStore()
vs.load_from_s3()
print('Index loaded:', vs.vector_store.index.ntotal)
results = vs.similarity_search('こんにちは', k=5)
print('Search results:', len(results))
"
```

---

### Step 3.4: Set Up LangChain RAG
**Objective**: Build RAG pipeline with LangChain

**Tasks**:
1. Set up LangChain Bedrock embeddings wrapper
2. Integrate FAISS vector store with LangChain
3. Create RAG chain with conversation memory
4. Create custom prompt template for Japanese learning context
5. Test RAG retrieval and response generation

**Test Criteria**:
- ✅ RAG chain works
- ✅ Retrieves relevant context from FAISS
- ✅ Conversation memory works across turns
- ✅ Response quality is good

**Files to Create**:
- `app/api/v1/chat/integrations/bedrock_embeddings.py`
- `app/api/v1/chat/services/rag_service.py`

**Bedrock Embeddings Wrapper** (already created in vector_store.py, but can be separate):
```python
# app/api/v1/chat/integrations/bedrock_embeddings.py
from langchain_aws import BedrockEmbeddings
import os
import logging

logger = logging.getLogger(__name__)

class BedrockEmbeddingService:
    def __init__(self):
        self.embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v1",
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
    
    def embed_query(self, text: str) -> list:
        """Generate embedding for a query"""
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, texts: list) -> list:
        """Generate embeddings for multiple documents"""
        return self.embeddings.embed_documents(texts)
```

**RAG Service Implementation**:
```python
# app/api/v1/chat/services/rag_service.py
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_aws import ChatBedrock
from langchain_community.chat_models import ChatGoogleGenerativeAI
import os
import logging
from typing import Dict, List, Optional
from integrations.vector_store import FAISSVectorStore

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.vector_store: Optional[FAISSVectorStore] = None
        self.chain: Optional[ConversationalRetrievalChain] = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
    
    def initialize(self):
        """Initialize RAG service - load FAISS index and create chain"""
        if self.chain:
            return  # Already initialized
        
        logger.info("Initializing RAG service...")
        
        # Load vector store
        self.vector_store = FAISSVectorStore()
        if not self.vector_store.load_from_s3():
            logger.warning("Could not load FAISS index from S3, building from DynamoDB...")
            self.vector_store.build_index_from_dynamodb()
            self.vector_store.save_to_s3()
        
        # Create retriever
        retriever = self.vector_store.vector_store.as_retriever(
            search_kwargs={"k": 5}  # Retrieve top 5 similar items
        )
        
        # Create LLM (using Gemini for now, can switch to Bedrock)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=os.getenv('GEMINI_API_KEY')
        )
        
        # Custom prompt template
        template = """You are a helpful AI assistant for a Japanese language learning application.

Use the following pieces of context to answer the user's question about Japanese words, kanjis, sentences, or grammar.
If you don't know the answer based on the context, say so. Don't make up information.

Context from database:
{context}

Chat history:
{chat_history}

User question: {question}

Provide a helpful and accurate answer in the user's preferred language (default: English):"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "chat_history", "question"]
        )
        
        # Create RAG chain
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": prompt},
            return_source_documents=True,
            verbose=True
        )
        
        logger.info("RAG service initialized")
    
    def chat(self, question: str, user_context: Optional[Dict] = None) -> Dict:
        """
        Process chat question with RAG
        
        Args:
            question: User's question
            user_context: Optional user learning context
            
        Returns:
            {
                'answer': str,
                'source_documents': List[Document],
                'chat_history': List
            }
        """
        if not self.chain:
            self.initialize()
        
        # Enhance question with user context if provided
        if user_context:
            enhanced_question = f"""
User context: {user_context.get('summary', '')}

Question: {question}
"""
        else:
            enhanced_question = question
        
        try:
            result = self.chain.invoke({"question": enhanced_question})
            return {
                'answer': result['answer'],
                'source_documents': result.get('source_documents', []),
                'chat_history': self.memory.chat_memory.messages
            }
        except Exception as e:
            logger.error(f"Error in RAG chat: {str(e)}")
            raise
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
```

**Test Command**:
```python
from app.api.v1.chat.services.rag_service import RAGService

service = RAGService()
service.initialize()
response = service.chat("What does こんにちは mean?")
print(response['answer'])
assert len(response['answer']) > 0
```

---

### Step 3.5: Create Tool Functions
**Objective**: Enable tool calling to DynamoDB

**Tasks**:
1. Create DynamoDB tool functions (words, kanjis, sentences)
2. Create user progress/plan tool functions
3. Register tools with LangChain
4. Integrate tools with Gemini API (Function Calling)

**Test Criteria**:
- ✅ All tool functions created
- ✅ Tools can be called
- ✅ Gemini API invokes tools correctly

**Files to Create**:
- `app/api/v1/chat/tools/dynamodb_tools.py`
- `app/api/v1/chat/tools/user_progress_tools.py`

---

### Step 3.6: Integrate RAG with Chat
**Objective**: Use RAG context in chat responses

**Tasks**:
1. Integrate RAG service into chat endpoint
2. Retrieve context for user questions
3. Inject context into Gemini API prompt
4. Handle tool calls from Gemini API
5. Inject user context (progress, plan)

**Test Criteria**:
- ✅ RAG context is retrieved
- ✅ Context improves responses
- ✅ Tool calling works
- ✅ User context is used

**Files to Modify**:
- `app/api/v1/chat/endpoints/chat.py` (integrate RAG)
- `app/api/v1/chat/services/rag_service.py`
- `app/api/v1/chat/services/user_context_service.py` (new)

---

## Phase 4: Real-time Text Chat (WebSocket) - *Timing TBD*

**Objective**: Upgrade to real-time text chat using WebSocket

**Scope**:
- ✅ Replace REST API with WebSocket API Gateway
- ✅ Real-time bidirectional text streaming
- ✅ Keep all RAG/DB features from Phase 3
- ✅ Maintain conversation logging

**When to Introduce**: 
- **Recommended**: After Phase 3 is stable and tested
- **Alternative**: Can be introduced earlier if real-time is critical

**Timeline**: 3-4 days

---

### Step 4.1: Set Up WebSocket API Gateway
**Objective**: Configure WebSocket API

**Tasks**:
1. Create WebSocket API Gateway in template.yaml
2. Configure routes ($connect, $disconnect, $default)
3. Set up Lambda integration
4. Configure connection state management

**Test Criteria**:
- ✅ WebSocket API is created
- ✅ Routes are configured
- ✅ Can establish WebSocket connection

**Files to Modify**:
- `template.yaml`

---

### Step 4.2: Migrate Chat to WebSocket
**Objective**: Move chat logic to WebSocket handler

**Tasks**:
1. Create Lambda handler for WebSocket events
2. Migrate chat logic from REST to WebSocket
3. Handle connection lifecycle
4. Stream responses in real-time
5. Maintain RAG integration

**Test Criteria**:
- ✅ WebSocket chat works
- ✅ Real-time streaming works
- ✅ RAG still works
- ✅ Logging still works

**Files to Create**:
- `app/api/v1/chat/websocket/handler.py`
- `app/api/v1/chat/websocket/connection_manager.py`

**Files to Modify**:
- `app/api/v1/chat/app.py` (WebSocket handler)

---

## Phase 5: Real-time Voice Chat (WebSocket) - *Timing TBD*

**Objective**: Add voice input/output to real-time chat

**Scope**:
- ✅ Upgrade to Gemini 2.5 Flash Live API
- ✅ Real-time audio streaming
- ✅ Voice Activity Detection (built-in)
- ✅ Turn-taking (built-in)
- ✅ Keep all features from Phase 4

**When to Introduce**:
- **Recommended**: After Phase 4 is stable
- **Alternative**: Can skip Phase 4 and go directly from Phase 3 to Phase 5

**Timeline**: 3-4 days

---

### Step 5.1: Upgrade to Gemini Live API
**Objective**: Switch from Gemini API to Gemini Live API

**Tasks**:
1. Set up Gemini 2.5 Flash Live API access (Vertex AI)
2. Configure WebSocket connection to Gemini Live API
3. Handle bidirectional audio streaming
4. Test basic voice chat

**Test Criteria**:
- ✅ Gemini Live API connection works
- ✅ Audio streaming works
- ✅ Voice input/output works

**Files to Create**:
- `app/api/v1/chat/integrations/gemini_live_client.py`

**Files to Modify**:
- `app/api/v1/chat/websocket/handler.py` (integrate Live API)

---

### Step 5.2: Integrate Voice with RAG
**Objective**: Use RAG context in voice chat

**Tasks**:
1. Integrate RAG service with Gemini Live API
2. Inject context into Live API sessions
3. Handle tool calls in voice mode
4. Maintain conversation logging

**Test Criteria**:
- ✅ RAG context works in voice chat
- ✅ Tool calling works in voice mode
- ✅ Logging works for voice conversations

**Files to Modify**:
- `app/api/v1/chat/services/gemini_live_rag_service.py`

---

## Recommendations: When to Introduce WebSocket and Voice

### **Option A: Incremental (Recommended)**

**Timeline**:
1. Phase 1-2: REST API text chat (4-6 days)
2. Phase 3: REST API + RAG (8-12 days)
3. **Test and stabilize** (2-3 days)
4. Phase 4: WebSocket real-time text (3-4 days)
5. **Test and stabilize** (2-3 days)
6. Phase 5: WebSocket real-time voice (3-4 days)

**Total**: 22-32 days

**Advantages**:
- ✅ Each phase is independently testable
- ✅ Can deploy and get user feedback at each stage
- ✅ Lower risk - issues are isolated to specific phases
- ✅ Can skip phases if not needed

**When to Introduce WebSocket (Phase 4)**:
- ✅ After Phase 3 is stable and tested
- ✅ When real-time experience becomes important
- ✅ When you have bandwidth for WebSocket complexity

**When to Introduce Voice (Phase 5)**:
- ✅ After Phase 4 is stable (if doing Phase 4)
- ✅ OR directly after Phase 3 (if skipping Phase 4)
- ✅ When voice chat is a priority feature

---

### **Option B: Skip WebSocket Text, Go Directly to Voice**

**Timeline**:
1. Phase 1-2: REST API text chat (4-6 days)
2. Phase 3: REST API + RAG (8-12 days)
3. **Test and stabilize** (2-3 days)
4. Phase 5: WebSocket real-time voice (3-4 days) - *Skip Phase 4*

**Total**: 17-25 days

**Advantages**:
- ✅ Faster to voice chat
- ✅ Gemini Live API handles both text and voice
- ✅ One WebSocket implementation instead of two

**When to Use This**:
- ✅ Voice chat is high priority
- ✅ Real-time text is not critical
- ✅ Want to minimize development phases

**Considerations**:
- ⚠️ WebSocket complexity comes earlier
- ⚠️ Less incremental testing opportunity

---

### **Option C: Start with WebSocket from Phase 1**

**Timeline**:
1. Phase 1: WebSocket text chat (3-4 days)
2. Phase 2: WebSocket text + logging (2-3 days)
3. Phase 3: WebSocket text + RAG (8-12 days)
4. Phase 5: WebSocket voice (3-4 days)

**Total**: 16-23 days

**Advantages**:
- ✅ Real-time from the start
- ✅ No migration needed later
- ✅ Consistent architecture

**When to Use This**:
- ✅ Real-time is critical from day one
- ✅ Team is comfortable with WebSocket
- ✅ Want to avoid REST → WebSocket migration

**Considerations**:
- ⚠️ More complex from the start
- ⚠️ Harder to debug initially
- ⚠️ Less incremental testing

---

## Recommended Approach: **Option A (Incremental)**

**Rationale**:
1. **Lower Risk**: REST API is simpler to debug and test
2. **Faster Initial Delivery**: Phase 1-2 can be deployed quickly
3. **User Feedback**: Get feedback early, iterate based on needs
4. **Flexibility**: Can skip Phase 4 if real-time text isn't needed
5. **Learning Curve**: Team learns WebSocket complexity gradually

**Decision Points**:

**After Phase 3**:
- ✅ If REST API text chat meets needs → **Stop here** (or add Phase 4 later)
- ✅ If real-time text is needed → **Proceed to Phase 4**
- ✅ If voice is priority → **Skip Phase 4, go to Phase 5**

**After Phase 4**:
- ✅ If real-time text meets needs → **Stop here**
- ✅ If voice is needed → **Proceed to Phase 5**

---

## Implementation Checklist

### Phase 1: Simple Text Chat
- [ ] Set up Gemini API access
- [ ] Create REST API endpoint
- [ ] Deploy to AWS
- [ ] Test basic chat

### Phase 2: Text Chat + Logging
- [ ] Create conversation logging
- [ ] Create conversation summarizer
- [ ] Create admin endpoints
- [ ] Test admin access

### Phase 3: Full RAG Chat
- [ ] Set up RAG infrastructure
- [ ] Generate embeddings
- [ ] Build FAISS index
- [ ] Set up LangChain RAG
- [ ] Create tool functions
- [ ] Integrate RAG with chat

### Phase 4: WebSocket Real-time Text (Optional)
- [ ] Set up WebSocket API Gateway
- [ ] Migrate chat to WebSocket
- [ ] Test real-time streaming

### Phase 5: WebSocket Real-time Voice (Optional)
- [ ] Upgrade to Gemini Live API
- [ ] Integrate voice with RAG
- [ ] Test voice chat

---

## Timeline Estimate

| Phase | Duration | Dependencies | Optional? |
|-------|----------|--------------|-----------|
| Phase 1: Simple Text Chat | 2-3 days | None | No |
| Phase 2: Text Chat + Logging | 2-3 days | Phase 1 | No |
| Phase 3: Full RAG Chat | 8-12 days | Phase 2 | No |
| Phase 4: WebSocket Text | 3-4 days | Phase 3 | **Yes** |
| Phase 5: WebSocket Voice | 3-4 days | Phase 3 or 4 | **Yes** |

**Minimum (Phases 1-3)**: 12-18 days (2.5-3.5 weeks)
**With WebSocket Text (Phases 1-4)**: 15-22 days (3-4.5 weeks)
**Full Implementation (Phases 1-5)**: 18-26 days (3.5-5 weeks)

---

## Cost Progression

**Phase 1-2**: < $1/month
- Gemini API: ~$0.50/month (text only, low usage)

**Phase 3**: < $2/month
- Gemini API: ~$0.50/month
- Bedrock embeddings: < $1/month
- DynamoDB/S3: < $0.50/month

**Phase 4**: +$0.50/month
- WebSocket API Gateway: minimal
- Same Gemini API costs

**Phase 5**: +$2-4/month
- Gemini Live API: ~$0.0675 per 5-minute voice session
- 30-50 sessions/month: ~$2-4/month

**Total (Full)**: ~$4-7/month

---

## Success Criteria by Phase

### Phase 1
- ✅ Basic text chat works
- ✅ REST API endpoint responds
- ✅ No errors in production

### Phase 2
- ✅ Conversations are logged
- ✅ Summaries are generated
- ✅ Admins can view conversations

### Phase 3
- ✅ Chatbot uses app data (words, kanjis, sentences)
- ✅ Responses are accurate and contextual
- ✅ Tool calling works
- ✅ User progress is accessible

### Phase 4
- ✅ Real-time text streaming works
- ✅ Lower latency than REST API
- ✅ All Phase 3 features still work

### Phase 5
- ✅ Voice input/output works
- ✅ Hands-free conversation works
- ✅ All Phase 3-4 features still work

---

## Next Steps

1. **Start with Phase 1**: Get basic chat working quickly
2. **Deploy Phase 1-2**: Get user feedback early
3. **Evaluate after Phase 3**: Decide if WebSocket/voice is needed
4. **Proceed incrementally**: Add WebSocket/voice when ready

**Key Advantage**: Each phase delivers value independently, allowing flexible deployment based on priorities! 🚀

---

## Deployability and Testability Assessment

### ✅ Phase 1: Simple Text Chat - **FULLY DEPLOYABLE & TESTABLE**

**Deployment Readiness**:
- ✅ Complete SAM template configuration (Step 1.3)
- ✅ All dependencies listed (`requirements.txt`)
- ✅ IAM permissions configured
- ✅ Environment variables defined
- ✅ REST API Gateway configured

**Testability**:
- ✅ Test criteria defined for each step
- ✅ Test commands provided (Python unit tests, curl commands)
- ✅ Can be deployed independently: `sam build && sam deploy`
- ✅ No dependencies on other phases

**Deployment Command**:
```bash
# Step 1.3: Deploy Phase 1
sam build
sam deploy --guided
# Test: curl -X POST https://api.example.com/api/v1/chat/message ...
```

---

### ✅ Phase 2: Text Chat + Logging - **FULLY DEPLOYABLE & TESTABLE**

**Deployment Readiness**:
- ✅ DynamoDB table schema defined (ConversationLogsTable)
- ✅ Admin function SAM template configuration
- ✅ All code implementations provided
- ✅ IAM permissions for DynamoDB writes
- ✅ Builds on Phase 1 (incremental)

**Testability**:
- ✅ Test criteria for logging, summarization, admin endpoints
- ✅ Can test independently after Phase 1 deployment
- ✅ Admin endpoints testable via curl/Postman

**Deployment Command**:
```bash
# After Phase 1 is deployed, deploy Phase 2 additions
sam build
sam deploy
# Test: Check DynamoDB for conversation logs
# Test: GET /api/v1/admin/chat/conversations
```

---

### ⚠️ Phase 3: Full RAG Chat - **PARTIALLY DEPLOYABLE & TESTABLE**

**Deployment Readiness**:
- ✅ Steps 3.1-3.4: Complete implementations with SAM template updates
- ⚠️ Steps 3.5-3.6: **Missing detailed implementations** (referenced but not fully detailed)

**What's Complete**:
- ✅ Step 3.1: Infrastructure (S3 bucket, IAM, dependencies)
- ✅ Step 3.2: Embedding service + generation script
- ✅ Step 3.3: FAISS vector store + index builder
- ✅ Step 3.4: LangChain RAG service

**What's Missing Detail**:
- ⚠️ Step 3.5: Tool functions (dynamodb_tools.py, user_progress_tools.py) - **needs implementation**
- ⚠️ Step 3.6: RAG integration in chat endpoint - **needs implementation**

**Testability**:
- ✅ Steps 3.1-3.4: Test commands provided
- ⚠️ Steps 3.5-3.6: Test criteria defined but implementation code missing

**Deployment Command** (for Steps 3.1-3.4):
```bash
# Step 3.1: Update dependencies and deploy
sam build
sam deploy
# Step 3.2: Generate embeddings (local script)
python scripts/generate_embeddings.py --entity-type all
# Step 3.3: Build FAISS index (local script)
python scripts/build_faiss_index.py
# Step 3.4: Test RAG service
python -c "from app.api.v1.chat.services.rag_service import RAGService; ..."
```

**⚠️ Action Required**: Add detailed implementations for Steps 3.5-3.6 to make Phase 3 fully deployable.

---

### ⚠️ Phase 4: WebSocket Real-time Text - **NOT FULLY DEPLOYABLE**

**Deployment Readiness**:
- ⚠️ Step 4.1: WebSocket API Gateway configuration - **template.yaml details missing**
- ⚠️ Step 4.2: WebSocket handler implementation - **code missing**

**What's Missing**:
- ⚠️ Complete SAM template for WebSocket API Gateway
- ⚠️ Lambda handler code for WebSocket events
- ⚠️ Connection manager implementation
- ⚠️ Test commands for WebSocket

**Testability**:
- ⚠️ Test criteria defined but cannot test without implementations

**⚠️ Action Required**: Add detailed WebSocket implementation from original plan.

---

### ⚠️ Phase 5: Real-time Voice Chat - **NOT FULLY DEPLOYABLE**

**Deployment Readiness**:
- ⚠️ Step 5.1: Gemini Live API client - **code missing**
- ⚠️ Step 5.2: Voice + RAG integration - **code missing**

**What's Missing**:
- ⚠️ Gemini Live API client implementation
- ⚠️ Voice streaming handler
- ⚠️ Integration with existing RAG service

**Testability**:
- ⚠️ Test criteria defined but cannot test without implementations

**⚠️ Action Required**: Add detailed Gemini Live API implementation from original plan.

---

## Summary: Deployability Status

| Phase | Deployable? | Testable? | Status |
|-------|-------------|-----------|--------|
| **Phase 1** | ✅ Yes | ✅ Yes | **READY** |
| **Phase 2** | ✅ Yes | ✅ Yes | **READY** |
| **Phase 3** | ⚠️ Partial | ⚠️ Partial | **NEEDS Steps 3.5-3.6** |
| **Phase 4** | ❌ No | ❌ No | **NEEDS Implementation** |
| **Phase 5** | ❌ No | ❌ No | **NEEDS Implementation** |

## Recommendations

1. **Phases 1-2**: ✅ Ready to deploy and test immediately
2. **Phase 3**: Complete Steps 3.5-3.6 implementations (tool functions and RAG integration)
3. **Phases 4-5**: Add detailed implementations from original plan when ready

**Each phase CAN be deployed and tested independently once implementations are complete**, following the incremental approach outlined in the plan.

