# How to Read Conversation Logs

## Overview

You can read conversation logs in two ways:
1. **Direct DynamoDB Queries** (for developers/admins with AWS access)
2. **Admin API Endpoints** (for frontend/admin dashboard)

---

## Method 1: Direct DynamoDB Queries

### Using AWS CLI

#### Query 1: Get All Turns in a Session
```bash
aws dynamodb query \
  --table-name japanese-learn-chat-conversations \
  --key-condition-expression "sessionId = :sid" \
  --expression-attribute-values '{":sid":{"S":"550e8400-e29b-41d4-a716-446655440000"}}' \
  --region ap-northeast-1
```

**Output Example:**
```json
{
  "Items": [
    {
      "sessionId": {"S": "550e8400-e29b-41d4-a716-446655440000"},
      "timestamp": {"S": "2025-12-03T20:15:30.123456+00:00"},
      "userId": {"S": "user@example.com"},
      "question": {"S": "What does こんにちは mean?"},
      "response": {"S": "こんにちは (konnichiwa) means 'hello'..."},
      "messageType": {"S": "text"},
      "metadata": {"M": {}},
      "ttl": {"N": "1735852530"}
    },
    {
      "sessionId": {"S": "550e8400-e29b-41d4-a716-446655440000"},
      "timestamp": {"S": "2025-12-03T20:16:45.789012+00:00"},
      "userId": {"S": "user@example.com"},
      "question": {"S": "Can you give me more examples?"},
      "response": {"S": "Sure! Here are some other common..."},
      "messageType": {"S": "text"},
      "metadata": {"M": {}},
      "ttl": {"N": "1735852530"}
    }
  ]
}
```

#### Query 2: Get User's All Conversations (Using GSI)
```bash
aws dynamodb query \
  --table-name japanese-learn-chat-conversations \
  --index-name userId-timestamp-index \
  --key-condition-expression "userId = :uid" \
  --expression-attribute-values '{":uid":{"S":"user@example.com"}}' \
  --region ap-northeast-1 \
  --limit 100
```

#### Query 3: Get User's Conversations in Date Range
```bash
aws dynamodb query \
  --table-name japanese-learn-chat-conversations \
  --index-name userId-timestamp-index \
  --key-condition-expression "userId = :uid AND timestamp BETWEEN :start AND :end" \
  --expression-attribute-values '{
    ":uid":{"S":"user@example.com"},
    ":start":{"S":"2025-12-01T00:00:00+00:00"},
    ":end":{"S":"2025-12-31T23:59:59+00:00"}
  }' \
  --region ap-northeast-1
```

### Using Python (boto3)

```python
import boto3
from boto3.dynamodb.conditions import Key

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('japanese-learn-chat-conversations')

# Query 1: Get all turns in a session
def get_session_conversation(session_id: str):
    response = table.query(
        KeyConditionExpression=Key('sessionId').eq(session_id)
    )
    return response['Items']

# Query 2: Get user's conversations
def get_user_conversations(user_id: str, limit: int = 100):
    response = table.query(
        IndexName='userId-timestamp-index',
        KeyConditionExpression=Key('userId').eq(user_id),
        Limit=limit,
        ScanIndexForward=False  # Most recent first
    )
    return response['Items']

# Query 3: Get conversations in date range
def get_user_conversations_by_date(user_id: str, start_date: str, end_date: str):
    response = table.query(
        IndexName='userId-timestamp-index',
        KeyConditionExpression=Key('userId').eq(user_id) 
            & Key('timestamp').between(start_date, end_date)
    )
    return response['Items']

# Example usage
session_logs = get_session_conversation('550e8400-e29b-41d4-a716-446655440000')
user_logs = get_user_conversations('user@example.com', limit=50)
```

### Using AWS Console

1. Go to **DynamoDB** → **Tables** → `japanese-learn-chat-conversations`
2. Click **Explore table items**
3. Use **Query** tab:
   - **Partition key**: `sessionId` = `550e8400-e29b-41d4-a716-446655440000`
   - Click **Run**
4. Or use **Scan** tab to browse all items (less efficient)

---

## Method 2: Admin API Endpoints

### Endpoint 1: List All Conversations

```http
GET /api/v1/admin/chat/conversations?limit=100&page=1
Authorization: Bearer {admin-token}
```

**Response:**
```json
{
  "data": [
    {
      "sessionId": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-12-03T20:15:30.123456+00:00",
      "userId": "user@example.com",
      "question": "What does こんにちは mean?",
      "response": "こんにちは (konnichiwa) means 'hello'...",
      "messageType": "text",
      "metadata": {}
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 100,
    "total": 1250,
    "total_pages": 13,
    "has_next": true,
    "has_previous": false
  }
}
```

### Endpoint 2: Get User's Conversations

```http
GET /api/v1/admin/chat/conversations/user/user@example.com?limit=50
Authorization: Bearer {admin-token}
```

**Response:**
```json
{
  "data": [
    {
      "sessionId": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-12-03T20:15:30.123456+00:00",
      "userId": "user@example.com",
      "question": "What does こんにちは mean?",
      "response": "こんにちは (konnichiwa) means 'hello'...",
      "messageType": "text"
    }
  ]
}
```

### Endpoint 3: Get Specific Session

```http
GET /api/v1/admin/chat/conversations/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {admin-token}
```

**Response:**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "turns": [
    {
      "timestamp": "2025-12-03T20:15:30.123456+00:00",
      "question": "What does こんにちは mean?",
      "response": "こんにちは (konnichiwa) means 'hello'...",
      "messageType": "text"
    },
    {
      "timestamp": "2025-12-03T20:16:45.789012+00:00",
      "question": "Can you give me more examples?",
      "response": "Sure! Here are some other common...",
      "messageType": "text"
    }
  ],
  "userId": "user@example.com",
  "totalTurns": 2,
  "firstTurn": "2025-12-03T20:15:30.123456+00:00",
  "lastTurn": "2025-12-03T20:16:45.789012+00:00"
}
```

### Endpoint 4: Filter by Category/Date

```http
GET /api/v1/admin/chat/conversations?category=word_meaning&start_date=2025-12-01&end_date=2025-12-31
Authorization: Bearer {admin-token}
```

---

## Reading Logs in Comfortable Format

### Option A: Simple Text Format (No Summarization Needed)

If you just want to read the raw logs, you can format them like this:

```python
def format_conversation_logs(session_logs):
    """Format logs for easy reading"""
    output = []
    for log in sorted(session_logs, key=lambda x: x['timestamp']):
        output.append(f"""
Session: {log['sessionId']}
Time: {log['timestamp']}
User: {log['userId']}
---
Q: {log['question']}
A: {log['response']}
---
""")
    return "\n".join(output)
```

**Output:**
```
Session: 550e8400-e29b-41d4-a716-446655440000
Time: 2025-12-03T20:15:30.123456+00:00
User: user@example.com
---
Q: What does こんにちは mean?
A: こんにちは (konnichiwa) means 'hello' or 'good afternoon' in Japanese...
---

Session: 550e8400-e29b-41d4-a716-446655440000
Time: 2025-12-03T20:16:45.789012+00:00
User: user@example.com
---
Q: Can you give me more examples?
A: Sure! Here are some other common Japanese greetings...
---
```

### Option B: CSV Export

```python
import csv

def export_to_csv(logs, filename='conversations.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'User ID', 'Session ID', 'Question', 'Response'])
        for log in logs:
            writer.writerow([
                log['timestamp'],
                log['userId'],
                log['sessionId'],
                log['question'],
                log['response']
            ])
```

### Option C: JSON Export

```python
import json

def export_to_json(logs, filename='conversations.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
```

---

## Do You Need Summarization?

### **You DON'T need summarization if:**

1. ✅ **You want to read full conversations** - Raw logs show everything
2. ✅ **You have time to read through logs** - No need for quick overview
3. ✅ **You're doing detailed analysis** - Full text is better than summaries
4. ✅ **You want to save costs** - Summarization uses Gemini API (adds cost)
5. ✅ **You have good search/filter tools** - Can find what you need in raw logs

### **You DO need summarization if:**

1. ✅ **You want quick overview** - See 100 conversations in 5 minutes
2. ✅ **You need analytics/dashboards** - Category counts, topic trends
3. ✅ **You want to filter by category** - "Show me all grammar questions"
4. ✅ **You need searchable metadata** - Find conversations about "kanji" quickly
5. ✅ **You want statistics** - "Most common question types this month"

---

## Recommendation

### **Skip Summarization If:**
- You're comfortable reading raw logs
- You have good query/filter tools
- You want to minimize costs
- You need full conversation context

### **Use Summarization If:**
- You need analytics/dashboards
- You want to filter by category/topic
- You need quick overviews
- You want to generate reports

---

## Hybrid Approach (Best of Both Worlds)

You can:
1. **Store raw logs** (always useful)
2. **Generate summaries on-demand** (when needed for analytics)
3. **Cache summaries** (if frequently accessed)

This way:
- ✅ Full logs available when needed
- ✅ Summaries available for analytics
- ✅ No cost if summaries not needed
- ✅ Can generate summaries later if needed

---

## Example: Reading Logs Without Summarization

```python
# Simple script to read and display logs
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('japanese-learn-chat-conversations')

# Get all conversations for a user
user_id = 'user@example.com'
response = table.query(
    IndexName='userId-timestamp-index',
    KeyConditionExpression=Key('userId').eq(user_id),
    ScanIndexForward=False,  # Most recent first
    Limit=100
)

# Format for reading
for item in response['Items']:
    print(f"\n{'='*60}")
    print(f"Time: {item['timestamp']}")
    print(f"Session: {item['sessionId']}")
    print(f"{'-'*60}")
    print(f"Q: {item['question']}")
    print(f"A: {item['response'][:200]}...")  # First 200 chars
    print(f"{'='*60}\n")
```

**Output:**
```
============================================================
Time: 2025-12-03T20:15:30.123456+00:00
Session: 550e8400-e29b-41d4-a716-446655440000
------------------------------------------------------------
Q: What does こんにちは mean?
A: こんにちは (konnichiwa) means 'hello' or 'good afternoon' in Japanese. It's a common greeting used during the day...
============================================================
```

---

## Conclusion

**If you can read logs comfortably in raw format, you can skip summarization for now.** You can always add it later if you find you need:
- Quick overviews
- Analytics/dashboards
- Category-based filtering
- Statistical reports

The raw logs contain all the information - summaries are just a convenience feature for quick scanning and analytics.

