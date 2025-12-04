# Phase 3: Word/Kanji Detail Page Links Implementation

## Overview

This document describes how to implement the feature where the chatbot provides links to word/kanji detail pages when users ask questions like:
- "What does XXX mean?"
- "What is XXX in Japanese?"
- "What is the reading of XXX?"

## Implementation Strategy

### Approach: Gemini Function Calling + Tool Functions

1. **Create Tool Functions**: Functions that search for words/kanjis in DynamoDB
2. **Register with Gemini**: Use Gemini's native Function Calling feature
3. **Return Links**: Tool functions return data + frontend URLs
4. **Format Response**: Gemini includes links in its natural language response

---

## Step 1: Create Tool Functions for Word/Kanji Lookup

### File: `app/api/v1/chat/tools/dynamodb_tools.py`

```python
"""
Tool functions for DynamoDB queries
These functions are registered with Gemini API for function calling
"""
import boto3
import os
import logging
from typing import Dict, List, Optional, Any
from integrations.dynamodb_integration import DynamoDBClient

logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb_client = DynamoDBClient()

# Frontend base URL (configure via environment variable)
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'https://your-frontend-domain.com')

def get_word_detail_url(word_id: int) -> str:
    """Generate frontend URL for word detail page"""
    return f"{FRONTEND_BASE_URL}/words/{word_id}"

def get_kanji_detail_url(kanji_id: int) -> str:
    """Generate frontend URL for kanji detail page"""
    return f"{FRONTEND_BASE_URL}/kanjis/{kanji_id}"

def search_word_by_name(word_name: str) -> Dict[str, Any]:
    """
    Search for a word by name (Japanese or English)
    
    This function is called by Gemini when user asks about a word.
    
    Args:
        word_name: Word name to search (can be Japanese or English)
    
    Returns:
        {
            "found": bool,
            "word": {
                "id": int,
                "name": str,
                "hiragana": str,
                "english": str,
                "level": int,
                "detail_url": str  # Frontend URL
            } | None,
            "message": str
        }
    """
    try:
        # Search in DynamoDB using existing client
        # First, try exact match by name
        words = dynamodb_client.get_words(limit=100)  # Get all words (or use search if available)
        
        # Search for matching word (case-insensitive)
        word_name_lower = word_name.lower().strip()
        
        for word in words:
            # Check Japanese name
            if word.get('name') and word_name_lower in word.get('name', '').lower():
                return {
                    "found": True,
                    "word": {
                        "id": word.get('id'),
                        "name": word.get('name'),
                        "hiragana": word.get('hiragana', ''),
                        "english": word.get('english', ''),
                        "level": word.get('level', 0),
                        "detail_url": get_word_detail_url(word.get('id'))
                    },
                    "message": f"Found word: {word.get('name')}"
                }
            
            # Check English translation
            if word.get('english') and word_name_lower in word.get('english', '').lower():
                return {
                    "found": True,
                    "word": {
                        "id": word.get('id'),
                        "name": word.get('name'),
                        "hiragana": word.get('hiragana', ''),
                        "english": word.get('english', ''),
                        "level": word.get('level', 0),
                        "detail_url": get_word_detail_url(word.get('id'))
                    },
                    "message": f"Found word: {word.get('name')} ({word.get('english')})"
                }
        
        return {
            "found": False,
            "word": None,
            "message": f"Word '{word_name}' not found"
        }
    
    except Exception as e:
        logger.error(f"Error searching word '{word_name}': {str(e)}")
        return {
            "found": False,
            "word": None,
            "message": f"Error searching for word: {str(e)}"
        }

def get_word_by_id(word_id: int) -> Dict[str, Any]:
    """
    Get word details by ID
    
    Args:
        word_id: Word ID
    
    Returns:
        {
            "found": bool,
            "word": {
                "id": int,
                "name": str,
                "hiragana": str,
                "english": str,
                "level": int,
                "detail_url": str
            } | None,
            "message": str
        }
    """
    try:
        word = dynamodb_client.get_word_by_id(word_id)
        
        if word:
            return {
                "found": True,
                "word": {
                    "id": word.get('id'),
                    "name": word.get('name'),
                    "hiragana": word.get('hiragana', ''),
                    "english": word.get('english', ''),
                    "level": word.get('level', 0),
                    "detail_url": get_word_detail_url(word.get('id'))
                },
                "message": f"Found word: {word.get('name')}"
            }
        else:
            return {
                "found": False,
                "word": None,
                "message": f"Word with ID {word_id} not found"
            }
    
    except Exception as e:
        logger.error(f"Error getting word {word_id}: {str(e)}")
        return {
            "found": False,
            "word": None,
            "message": f"Error getting word: {str(e)}"
        }

def search_kanji_by_character(kanji_character: str) -> Dict[str, Any]:
    """
    Search for a kanji by character
    
    Args:
        kanji_character: Kanji character to search
    
    Returns:
        {
            "found": bool,
            "kanji": {
                "id": int,
                "kanji": str,
                "meaning": str,
                "reading": str,
                "detail_url": str
            } | None,
            "message": str
        }
    """
    try:
        # Import kanji client
        from integrations.dynamodb.kanji import DynamoDBKanjiClient
        kanji_client = DynamoDBKanjiClient()
        
        # Get all kanjis and search
        kanjis = kanji_client.get_kanjis(limit=1000)  # Adjust limit as needed
        
        kanji_char = kanji_character.strip()
        
        for kanji in kanjis:
            if kanji.get('kanji') == kanji_char:
                return {
                    "found": True,
                    "kanji": {
                        "id": kanji.get('id'),
                        "kanji": kanji.get('kanji'),
                        "meaning": kanji.get('meaning', ''),
                        "reading": kanji.get('reading', ''),
                        "detail_url": get_kanji_detail_url(kanji.get('id'))
                    },
                    "message": f"Found kanji: {kanji_char}"
                }
        
        return {
            "found": False,
            "kanji": None,
            "message": f"Kanji '{kanji_char}' not found"
        }
    
    except Exception as e:
        logger.error(f"Error searching kanji '{kanji_character}': {str(e)}")
        return {
            "found": False,
            "kanji": None,
            "message": f"Error searching for kanji: {str(e)}"
        }

# Tool function registry for Gemini
TOOL_FUNCTIONS = {
    "search_word_by_name": {
        "function": search_word_by_name,
        "description": "Search for a Japanese word by its name (Japanese or English). Use this when user asks 'What does XXX mean?' or 'What is XXX in Japanese?'",
        "parameters": {
            "type": "object",
            "properties": {
                "word_name": {
                    "type": "string",
                    "description": "The word name to search for (can be Japanese or English)"
                }
            },
            "required": ["word_name"]
        }
    },
    "get_word_by_id": {
        "function": get_word_by_id,
        "description": "Get detailed information about a word by its ID. Use this when you have a word ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "word_id": {
                    "type": "integer",
                    "description": "The word ID"
                }
            },
            "required": ["word_id"]
        }
    },
    "search_kanji_by_character": {
        "function": search_kanji_by_character,
        "description": "Search for a kanji by its character. Use this when user asks about a specific kanji character or its reading.",
        "parameters": {
            "type": "object",
            "properties": {
                "kanji_character": {
                    "type": "string",
                    "description": "The kanji character to search for"
                }
            },
            "required": ["kanji_character"]
        }
    }
}
```

---

## Step 2: Update Gemini Client to Support Function Calling

### File: `app/api/v1/chat/integrations/gemini_client.py` (Update)

```python
import google.generativeai as genai
import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        api_key = self._get_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.tools = []  # Will be populated with tool definitions
    
    def _get_api_key(self) -> str:
        """Get Gemini API key from environment variable"""
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            logger.info("Using GEMINI_API_KEY from environment variable")
            return api_key
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    def register_tools(self, tool_functions: Dict[str, Any]):
        """
        Register tool functions with Gemini
        
        Args:
            tool_functions: Dictionary of tool function definitions
        """
        from tools.dynamodb_tools import TOOL_FUNCTIONS
        
        # Convert tool functions to Gemini format
        gemini_tools = []
        
        for tool_name, tool_def in tool_functions.items():
            gemini_tool = {
                "function_declarations": [{
                    "name": tool_name,
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"]
                }]
            }
            gemini_tools.append(gemini_tool)
        
        # Update model with tools
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            tools=gemini_tools if gemini_tools else None
        )
        
        self.tools = tool_functions
        logger.info(f"Registered {len(tool_functions)} tools with Gemini")
    
    def chat_with_tools(
        self,
        message: str,
        conversation_history: Optional[List] = None,
        tool_functions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send message to Gemini API with tool calling support
        
        Args:
            message: User's message
            conversation_history: Optional list of previous messages
            tool_functions: Optional tool functions to register
        
        Returns:
            {
                "response": str,  # Chatbot response text
                "tool_calls": List[Dict],  # Tool calls made (if any)
                "tool_results": List[Dict]  # Tool call results (if any)
            }
        """
        try:
            # Register tools if provided
            if tool_functions:
                self.register_tools(tool_functions)
            
            # Start chat session
            if conversation_history:
                chat = self.model.start_chat(history=conversation_history)
            else:
                chat = self.model.start_chat()
            
            # Send message
            response = chat.send_message(message)
            
            # Check if response requires function calls
            tool_calls = []
            tool_results = []
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check for function calls
                if hasattr(candidate, 'content') and candidate.content:
                    parts = candidate.content.parts
                    
                    for part in parts:
                        if hasattr(part, 'function_call'):
                            # Function call detected
                            func_call = part.function_call
                            tool_calls.append({
                                "name": func_call.name,
                                "args": dict(func_call.args)
                            })
                            
                            # Execute function call
                            if self.tools and func_call.name in self.tools:
                                tool_func = self.tools[func_call.name]["function"]
                                args = dict(func_call.args)
                                
                                try:
                                    result = tool_func(**args)
                                    tool_results.append({
                                        "name": func_call.name,
                                        "result": result
                                    })
                                    
                                    # Send function result back to Gemini
                                    function_response = chat.send_message({
                                        "function_response": {
                                            "name": func_call.name,
                                            "response": result
                                        }
                                    })
                                    
                                    # Get final response after tool call
                                    response = function_response
                                
                                except Exception as e:
                                    logger.error(f"Error executing tool {func_call.name}: {str(e)}")
                                    tool_results.append({
                                        "name": func_call.name,
                                        "error": str(e)
                                    })
            
            # Extract response text
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            return {
                "response": response_text,
                "tool_calls": tool_calls,
                "tool_results": tool_results
            }
        
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
    
    def chat(self, message: str, conversation_history: Optional[List] = None) -> str:
        """
        Simple chat without tools (backward compatibility)
        """
        try:
            if conversation_history:
                chat = self.model.start_chat(history=conversation_history)
                response = chat.send_message(message)
            else:
                response = self.model.generate_content(message)
            
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
```

---

## Step 3: Update Chat Endpoint to Use Tools

### File: `app/api/v1/chat/endpoints/chat.py` (Update)

```python
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.chat import ChatMessageRequest, ChatMessageResponse
from integrations.gemini_client import GeminiClient
from services.conversation_logger import ConversationLogger
from tools.dynamodb_tools import TOOL_FUNCTIONS  # Import tool functions
from typing import Optional
import logging
import uuid
import os
import requests
from jose import jwt, JWTError

logger = logging.getLogger(__name__)
router = APIRouter()

# Optional bearer scheme
optional_bearer_scheme = HTTPBearer(auto_error=False)

def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_bearer_scheme)
) -> Optional[str]:
    """Optional authentication - returns user_id if token is valid, None otherwise"""
    if not credentials:
        logger.info("No authorization header - allowing anonymous access")
        return None
    
    try:
        token = credentials.credentials
        cognito_region = os.environ.get("AWS_REGION", "ap-northeast-1")
        cognito_user_pool_id = os.environ.get("COGNITO_USER_POOL_ID", "ap-northeast-1_WGOHW5Nx9")
        cognito_app_client_id = os.environ.get("COGNITO_APP_CLIENT_ID", "6kkiqk3qqjnisn96rgc3kne63p")
        cognito_issuer = f"https://cognito-idp.{cognito_region}.amazonaws.com/{cognito_user_pool_id}"
        cognito_jwks_url = f"{cognito_issuer}/.well-known/jwks.json"
        
        resp = requests.get(cognito_jwks_url)
        resp.raise_for_status()
        jwks = resp.json()
        
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=cognito_app_client_id,
            issuer=cognito_issuer,
            options={"verify_at_hash": False}
        )
        
        user_id = payload.get("email")
        if user_id:
            logger.info(f"Authenticated user: {user_id}")
            return user_id
        else:
            logger.warning("No email found in token payload - allowing anonymous access")
            return None
            
    except JWTError as e:
        logger.info(f"JWT validation failed: {e} - allowing anonymous access")
        return None
    except Exception as e:
        logger.warning(f"Error validating token: {e} - allowing anonymous access")
        return None

conversation_logger = ConversationLogger()

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Chat endpoint with tool calling support
    - If user asks about a word/kanji, tool functions will be called
    - Tool functions return data + detail page URLs
    - Gemini includes links in its response
    """
    try:
        client = GeminiClient()
        
        # Register tools for function calling
        client.register_tools(TOOL_FUNCTIONS)
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Use user_id if authenticated, otherwise use anonymous identifier
        effective_user_id = user_id if user_id else f"anonymous-{session_id}"
        logger.info(f"Chat request from user: {effective_user_id}")
        
        # Call Gemini API with tool support
        result = client.chat_with_tools(
            request.message,
            tool_functions=TOOL_FUNCTIONS
        )
        
        response_text = result["response"]
        
        # Log tool calls if any
        if result.get("tool_calls"):
            logger.info(f"Tool calls made: {result['tool_calls']}")
        
        # Log conversation
        try:
            conversation_logger.log_conversation(
                user_id=effective_user_id,
                session_id=session_id,
                question=request.message,
                response=response_text,
                message_type="text",
                metadata={
                    "tool_calls": result.get("tool_calls", []),
                    "tool_results": result.get("tool_results", [])
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log conversation: {e}")
        
        return ChatMessageResponse(
            response=response_text,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
```

---

## Step 4: Add Environment Variable for Frontend URL

### File: `template.yaml` (Update ChatFunction)

```yaml
ChatFunction:
  Properties:
    Environment:
      Variables:
        GEMINI_API_KEY: !Ref GeminiApiKey
        CONVERSATION_LOGS_TABLE_NAME: !Ref ConversationLogsTable
        DYNAMODB_TABLE_NAME: !Ref DynamoDBTable
        FRONTEND_BASE_URL: "https://your-frontend-domain.com"  # Add this
        LOG_LEVEL: INFO
```

---

## Step 5: Improve Word Search (Optional - Use Existing Search)

If you have a better search implementation, you can use it:

```python
# Option: Use existing search service if available
def search_word_by_name(word_name: str) -> Dict[str, Any]:
    """Improved search using existing search service"""
    try:
        from services.search_service import search_service
        
        # Search for word
        results = search_service.search_words(word_name, limit=1)
        
        if results and len(results) > 0:
            word = results[0]
            return {
                "found": True,
                "word": {
                    "id": word.get('id'),
                    "name": word.get('name'),
                    "hiragana": word.get('hiragana', ''),
                    "english": word.get('english', ''),
                    "level": word.get('level', 0),
                    "detail_url": get_word_detail_url(word.get('id'))
                },
                "message": f"Found word: {word.get('name')}"
            }
        else:
            return {
                "found": False,
                "word": None,
                "message": f"Word '{word_name}' not found"
            }
    except Exception as e:
        logger.error(f"Error searching word: {str(e)}")
        return {
            "found": False,
            "word": None,
            "message": f"Error searching: {str(e)}"
        }
```

---

## Step 6: Update Response Schema (Optional)

If you want to return structured data with links:

### File: `app/api/v1/chat/schemas/chat.py` (Update)

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    response: str
    session_id: str
    links: Optional[List[Dict[str, str]]] = None  # Optional: [{"type": "word", "url": "...", "text": "..."}]
```

---

## Example: How It Works

### User Question:
```
"What does こんにちは mean?"
```

### Flow:
1. **Gemini detects** this is a word meaning question
2. **Gemini calls** `search_word_by_name("こんにちは")`
3. **Tool function** searches DynamoDB and returns:
   ```json
   {
     "found": true,
     "word": {
       "id": 123,
       "name": "こんにちは",
       "hiragana": "こんにちは",
       "english": "hello",
       "level": 1,
       "detail_url": "https://your-frontend.com/words/123"
     }
   }
   ```
4. **Gemini receives** tool result and generates response:
   ```
   "こんにちは (konnichiwa) means 'hello' or 'good afternoon' in Japanese. 
   It's a common greeting used during the day.
   
   [View word details](https://your-frontend.com/words/123)"
   ```

---

## Testing

### Test Tool Functions Directly:
```python
from app.api.v1.chat.tools.dynamodb_tools import search_word_by_name

result = search_word_by_name("こんにちは")
print(result)
# Should return: {"found": True, "word": {...}, "detail_url": "..."}
```

### Test Chat with Tools:
```bash
curl -X POST https://api.example.com/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What does こんにちは mean?"}'
```

Expected response should include:
- Explanation of the word
- Link to word detail page

---

## Notes

1. **Frontend URL Format**: Update `FRONTEND_BASE_URL` in `template.yaml` to match your frontend domain
2. **Search Performance**: Current implementation scans all words. Consider using DynamoDB GSI or existing search service for better performance
3. **Link Format**: Gemini will include links in markdown format `[text](url)` in its response
4. **Error Handling**: Tool functions return error messages that Gemini can use in its response
5. **Multiple Matches**: Current implementation returns first match. Can be extended to return multiple matches

---

## Next Steps

1. ✅ Create `app/api/v1/chat/tools/dynamodb_tools.py`
2. ✅ Update `app/api/v1/chat/integrations/gemini_client.py`
3. ✅ Update `app/api/v1/chat/endpoints/chat.py`
4. ✅ Add `FRONTEND_BASE_URL` to `template.yaml`
5. ✅ Test with sample questions
6. ✅ Deploy and verify

---

## Integration with Phase 3 RAG

When implementing full RAG (Step 3.6), you can combine:
- **RAG context** from FAISS (similar words/kanjis)
- **Tool calls** for specific word/kanji lookups
- **Links** in responses

This provides both contextual information and direct links to detail pages!

