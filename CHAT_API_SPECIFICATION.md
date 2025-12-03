# Chat API Endpoint Specification

## Endpoint: POST /api/v1/chat/message

Simple text chat endpoint for AI chatbot. Supports both authenticated and anonymous users.

---

## Endpoint URL

**Production:**
```
https://{api-id}.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/chat/message
```

**Local Development:**
```
http://localhost:8000/api/v1/chat/message
```

*Note: Replace `{api-id}` with your actual API Gateway ID from deployment output.*

---

## HTTP Method

`POST`

---

## Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | `application/json` |
| `Authorization` | No | `Bearer {token}` - Optional. If provided and valid, user will be authenticated. If missing or invalid, request will be treated as anonymous. |

---

## Request Body

JSON object with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's message/question to the chatbot |
| `session_id` | string | No | Optional session ID for conversation continuity. If not provided, a new UUID will be generated and returned in the response. |

### Request Body Example

**With session_id:**
```json
{
  "message": "What does こんにちは mean?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Without session_id (new conversation):**
```json
{
  "message": "Hello, can you help me learn Japanese?"
}
```

---

## Response Format

### Success Response (200 OK)

```json
{
  "response": "Chatbot's response text",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | The chatbot's response to the user's message |
| `session_id` | string | Session ID for this conversation. Use this in subsequent requests to maintain conversation context. If you provided a `session_id` in the request, the same value will be returned. Otherwise, a new UUID will be generated. |

### Error Response (500 Internal Server Error)

```json
{
  "detail": "Chat error: {error message}"
}
```

---

## Example Requests

### Example 1: Anonymous User (No Authentication)

```bash
curl -X POST https://{api-id}.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does こんにちは mean?"
  }'
```

**Response:**
```json
{
  "response": "こんにちは (konnichiwa) means 'hello' or 'good afternoon' in Japanese. It's a common greeting used during the day.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Example 2: Authenticated User

```bash
curl -X POST https://{api-id}.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {your-cognito-token}" \
  -d '{
    "message": "What does こんにちは mean?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Response:**
```json
{
  "response": "こんにちは (konnichiwa) means 'hello' or 'good afternoon' in Japanese. It's a common greeting used during the day.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Example 3: JavaScript/Fetch Example

```javascript
async function sendChatMessage(message, sessionId = null, authToken = null) {
  const url = 'https://{api-id}.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/chat/message';
  
  const headers = {
    'Content-Type': 'application/json',
  };
  
  // Add authorization header if token is provided
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  
  const body = {
    message: message,
  };
  
  // Add session_id if provided
  if (sessionId) {
    body.session_id = sessionId;
  }
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
}

// Usage example
const result = await sendChatMessage("What does こんにちは mean?");
console.log('Response:', result.response);
console.log('Session ID:', result.session_id);

// Continue conversation with same session_id
const followUp = await sendChatMessage(
  "Can you give me more examples?",
  result.session_id
);
```

---

## Notes

1. **Authentication is Optional**: The endpoint works with or without authentication. Anonymous users can use the chatbot freely.

2. **Session Management**: Use the `session_id` returned in the response to maintain conversation context across multiple requests. If you don't provide a `session_id`, a new one will be generated for each request.

3. **CORS**: The endpoint supports CORS and can be called from web browsers.

4. **Error Handling**: Always check the response status code. A 200 status means success, while 500 indicates an error.

5. **Rate Limiting**: Be aware of API rate limits and implement appropriate retry logic with exponential backoff if needed.

---

## Current Implementation Status

- ✅ Basic text chat functionality
- ✅ Optional authentication support
- ✅ Session ID management
- ❌ Conversation history (not yet implemented - Phase 1)
- ❌ RAG with database access (not yet implemented - Phase 3)
- ❌ User progress integration (not yet implemented - Phase 3)

