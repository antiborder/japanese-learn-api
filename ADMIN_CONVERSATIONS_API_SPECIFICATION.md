# Admin Conversations API Specification

## Overview

This document describes the admin endpoints for viewing conversation logs from the chatbot feature. All endpoints require **admin authentication**.

**Base URL:** `https://{api-id}.execute-api.ap-northeast-1.amazonaws.com/Prod`

**Authentication:** All endpoints require a valid JWT token with admin privileges in the `Authorization` header.

---

## 1. Get All Conversations

Retrieve a paginated list of all conversations.

### Endpoint

```
GET /api/v1/admin/chat/conversations
```

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token: `Bearer {JWT_TOKEN}` |
| `Content-Type` | Yes | `application/json` |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 100 | Number of conversations to return (1-1000) |
| `start_key` | string | No | - | Pagination token (JSON-encoded) for next page |
| `category` | string | No | - | Filter by category (only works if summarization is implemented) |

### Response Format

**Status Code:** `200 OK`

**Response Body:**
```json
[
  {
    "sessionId": "string",
    "timestamp": "string (ISO 8601)",
    "userId": "string",
    "question": "string",
    "response": "string",
    "summary": {
      "category": "string (optional)",
      "topics": ["string"] (optional),
      "response_type": "string (optional)",
      "key_points": ["string"] (optional)
    } | null,
    "messageType": "text"
  },
  ...
]
```

### Example Request

```bash
curl -X GET \
  "https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations?limit=50" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Example Response

```json
[
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-04T05:00:00.000Z",
    "userId": "bafjkfgbka@gmail.com",
    "question": "What is the meaning of こんにちは?",
    "response": "こんにちは (konnichiwa) means 'hello' or 'good afternoon' in Japanese. It's a common greeting used during the day.",
    "summary": null,
    "messageType": "text"
  },
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2025-12-04T05:01:00.000Z",
    "userId": "anonymous-550e8400-e29b-41d4-a716-446655440001",
    "question": "How do I say thank you?",
    "response": "In Japanese, 'thank you' is ありがとう (arigatou) for casual situations, or ありがとうございます (arigatou gozaimasu) for more formal situations.",
    "summary": null,
    "messageType": "text"
  }
]
```

### Error Responses

| Status Code | Description |
|-------------|-------------|
| `401 Unauthorized` | Invalid or missing authentication token |
| `403 Forbidden` | User is not an admin |
| `500 Internal Server Error` | Server error |

---

## 2. Get Conversations by User ID

Retrieve all conversations for a specific user.

### Endpoint

```
GET /api/v1/admin/chat/conversations/user/{user_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User ID (email address or anonymous identifier) |

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token: `Bearer {JWT_TOKEN}` |
| `Content-Type` | Yes | `application/json` |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 100 | Number of conversations to return (1-1000) |

### Response Format

**Status Code:** `200 OK`

**Response Body:**
```json
[
  {
    "sessionId": "string",
    "timestamp": "string (ISO 8601)",
    "userId": "string",
    "question": "string",
    "response": "string",
    "summary": {
      "category": "string (optional)",
      "topics": ["string"] (optional),
      "response_type": "string (optional)",
      "key_points": ["string"] (optional)
    } | null,
    "messageType": "text"
  },
  ...
]
```

**Note:** Results are sorted by timestamp in descending order (most recent first).

### Example Request

```bash
curl -X GET \
  "https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations/user/bafjkfgbka@gmail.com?limit=20" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Example Response

```json
[
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-04T05:00:00.000Z",
    "userId": "bafjkfgbka@gmail.com",
    "question": "What is the meaning of こんにちは?",
    "response": "こんにちは (konnichiwa) means 'hello' or 'good afternoon' in Japanese.",
    "summary": null,
    "messageType": "text"
  },
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2025-12-04T04:50:00.000Z",
    "userId": "bafjkfgbka@gmail.com",
    "question": "How do I conjugate verbs?",
    "response": "Japanese verbs have different conjugation patterns...",
    "summary": null,
    "messageType": "text"
  }
]
```

### Error Responses

| Status Code | Description |
|-------------|-------------|
| `401 Unauthorized` | Invalid or missing authentication token |
| `403 Forbidden` | User is not an admin |
| `500 Internal Server Error` | Server error |

---

## 3. Get Conversations by Session ID

Retrieve all messages in a specific conversation session.

### Endpoint

```
GET /api/v1/admin/chat/conversations/{session_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Session ID (UUID format) |

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token: `Bearer {JWT_TOKEN}` |
| `Content-Type` | Yes | `application/json` |

### Response Format

**Status Code:** `200 OK`

**Response Body:**
```json
[
  {
    "sessionId": "string",
    "timestamp": "string (ISO 8601)",
    "userId": "string",
    "question": "string",
    "response": "string",
    "summary": {
      "category": "string (optional)",
      "topics": ["string"] (optional),
      "response_type": "string (optional)",
      "key_points": ["string"] (optional)
    } | null,
    "messageType": "text",
    "metadata": {
      "key": "value"
    } | null
  },
  ...
]
```

**Note:** 
- Results are sorted by timestamp in ascending order (oldest first).
- This endpoint returns the full `ConversationResponse` model, which includes the `metadata` field.

### Example Request

```bash
curl -X GET \
  "https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Example Response

```json
[
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-04T05:00:00.000Z",
    "userId": "bafjkfgbka@gmail.com",
    "question": "What is the meaning of こんにちは?",
    "response": "こんにちは (konnichiwa) means 'hello' or 'good afternoon' in Japanese.",
    "summary": null,
    "messageType": "text",
    "metadata": {}
  },
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-04T05:01:00.000Z",
    "userId": "bafjkfgbka@gmail.com",
    "question": "Can you give me an example?",
    "response": "Sure! Here's an example: こんにちは、元気ですか？ (Konnichiwa, genki desu ka?) means 'Hello, how are you?'",
    "summary": null,
    "messageType": "text",
    "metadata": {}
  }
]
```

### Error Responses

| Status Code | Description |
|-------------|-------------|
| `401 Unauthorized` | Invalid or missing authentication token |
| `403 Forbidden` | User is not an admin |
| `404 Not Found` | Session ID not found |
| `500 Internal Server Error` | Server error |

---

## Data Models

### ConversationSummary

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sessionId` | string | Yes | Unique session identifier (UUID) |
| `timestamp` | string | Yes | ISO 8601 timestamp of the conversation |
| `userId` | string | Yes | User ID (email or `anonymous-{sessionId}`) |
| `question` | string | Yes | User's question |
| `response` | string | Yes | Chatbot's response |
| `summary` | object \| null | No | Optional summary object (if Step 2.2 is implemented) |
| `messageType` | string | Yes | Message type: `"text"` or `"voice"` |

### ConversationResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sessionId` | string | Yes | Unique session identifier (UUID) |
| `timestamp` | string | Yes | ISO 8601 timestamp of the conversation |
| `userId` | string | Yes | User ID (email or `anonymous-{sessionId}`) |
| `question` | string | Yes | User's question |
| `response` | string | Yes | Chatbot's response |
| `summary` | object \| null | No | Optional summary object (if Step 2.2 is implemented) |
| `messageType` | string | Yes | Message type: `"text"` or `"voice"` |
| `metadata` | object \| null | No | Additional metadata |

### Summary Object (Optional)

The `summary` field is only present if conversation summarization (Step 2.2) is implemented. It contains:

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | Category of the conversation (e.g., "grammar", "vocabulary") |
| `topics` | array of strings | List of topics discussed |
| `response_type` | string | Type of response (e.g., "explanation", "example") |
| `key_points` | array of strings | Key points from the conversation |

---

## Authentication

All endpoints require admin authentication. See [ADMIN_AUTHENTICATION_GUIDE.md](./ADMIN_AUTHENTICATION_GUIDE.md) for details on:

- How to obtain admin access
- Token requirements
- Admin check methods (ADMIN_EMAILS, Cognito groups, custom claims)

---

## Pagination

### Get All Conversations

The `GET /api/v1/admin/chat/conversations` endpoint supports pagination using the `start_key` parameter:

1. **First Request:** Omit `start_key` to get the first page
2. **Subsequent Requests:** Use the `start_key` from the previous response (if available) to get the next page

**Note:** The current implementation uses DynamoDB `scan`, which may not return a `start_key` in all cases. For better pagination, consider implementing cursor-based pagination.

### Get Conversations by User ID

The `GET /api/v1/admin/chat/conversations/user/{user_id}` endpoint uses DynamoDB `query` with a limit. Results are sorted by timestamp in descending order (most recent first).

---

## JavaScript/TypeScript Examples

### Get All Conversations

```typescript
async function getAllConversations(limit: number = 100, startKey?: string) {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (startKey) {
    params.append('start_key', startKey);
  }
  
  const response = await fetch(
    `https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations?${params}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${yourJwtToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}
```

### Get User Conversations

```typescript
async function getUserConversations(userId: string, limit: number = 100) {
  const response = await fetch(
    `https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations/user/${encodeURIComponent(userId)}?limit=${limit}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${yourJwtToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}
```

### Get Session Conversations

```typescript
async function getSessionConversations(sessionId: string) {
  const response = await fetch(
    `https://omqihdsdi1.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations/${sessionId}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${yourJwtToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Session not found');
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}
```

---

## Notes

1. **Summary Field:** The `summary` field is currently `null` for all conversations. It will be populated when Step 2.2 (Conversation Summarization) is implemented.

2. **Anonymous Users:** Users who access the chatbot without authentication will have a `userId` in the format `anonymous-{sessionId}`.

3. **Timestamp Format:** All timestamps are in ISO 8601 format (e.g., `2025-12-04T05:00:00.000Z`).

4. **CORS:** All endpoints support CORS and can be called from browser-based frontend applications.

5. **Rate Limiting:** Currently, there are no rate limits, but consider implementing them for production use.

