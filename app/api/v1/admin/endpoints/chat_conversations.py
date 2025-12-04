from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import boto3
import os
import json
from schemas.conversation import ConversationSummary, ConversationResponse, ConversationStats
from common.auth.admin_auth import require_admin_role
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize DynamoDB - region is automatically available in Lambda
dynamodb = boto3.resource('dynamodb')
conversations_table_name = os.getenv('CONVERSATION_LOGS_TABLE_NAME')
if conversations_table_name:
    conversations_table = dynamodb.Table(conversations_table_name)  # type: ignore
else:
    conversations_table = None
    logger.warning("CONVERSATION_LOGS_TABLE_NAME not set, admin endpoints will not work")

@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    limit: int = Query(100, ge=1, le=1000),
    start_key: Optional[str] = None,
    category: Optional[str] = None,  # Only works if Step 2.2 (summarization) is implemented
    admin_user: str = Depends(require_admin_role)  # Admin authentication required
):
    """
    List all conversations (admin only)
    Returns raw conversation logs with optional summaries
    """
    if not conversations_table:
        raise HTTPException(status_code=500, detail="Conversation logs table not configured")
    
    try:
        # Scan table with pagination
        scan_kwargs = {
            'Limit': limit
        }
        
        if start_key:
            try:
                scan_kwargs['ExclusiveStartKey'] = json.loads(start_key)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid start_key format")
        
        response = conversations_table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        # Filter by category if provided (requires summaries)
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
                response=item['response'],  # Always include full response
                summary=item.get('summary'),  # Optional: only if Step 2.2 implemented
                messageType=item.get('messageType', 'text')
            ))
        
        return conversations
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/user/{user_id}", response_model=List[ConversationSummary])
async def get_user_conversations(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    admin_user: str = Depends(require_admin_role)  # Admin authentication required
):
    """Get conversations for a specific user (admin only) - returns raw logs"""
    if not conversations_table:
        raise HTTPException(status_code=500, detail="Conversation logs table not configured")
    
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
                response=item['response'],  # Always include full response
                summary=item.get('summary'),  # Optional: only if Step 2.2 implemented
                messageType=item.get('messageType', 'text')
            ))
        
        return conversations
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{session_id}", response_model=List[ConversationResponse])
async def get_conversation(
    session_id: str,
    admin_user: str = Depends(require_admin_role)  # Admin authentication required
):
    """Get all turns in a specific conversation session (admin only) - returns raw logs"""
    if not conversations_table:
        raise HTTPException(status_code=500, detail="Conversation logs table not configured")
    
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
        
        # Sort by timestamp (chronological order)
        items = sorted(items, key=lambda x: x['timestamp'])
        
        # Return all turns in the session
        conversations = []
        for item in items:
            conversations.append(ConversationResponse(
                sessionId=item['sessionId'],
                timestamp=item['timestamp'],
                userId=item['userId'],
                question=item['question'],
                response=item['response'],
                summary=item.get('summary'),  # Optional: only if Step 2.2 implemented
                messageType=item.get('messageType', 'text'),
                metadata=item.get('metadata')
            ))
        
        return conversations
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summaries", response_model=List[ConversationSummary])
async def get_conversation_summaries(
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,  # Only works if Step 2.2 (summarization) is implemented
    admin_user: str = Depends(require_admin_role)  # Admin authentication required
):
    """
    Get conversation summaries only (admin only)
    ⚠️ Requires Step 2.2 (Conversation Summarizer) to be implemented
    Returns empty list if summaries are not available
    """
    if not conversations_table:
        raise HTTPException(status_code=500, detail="Conversation logs table not configured")
    
    try:
        # Similar to list_conversations but only return items with summaries
        scan_kwargs = {'Limit': limit}
        response = conversations_table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        # Filter items that have summaries
        items = [item for item in items if item.get('summary')]
        
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
                response=item['response'],  # Always include full response
                summary=item.get('summary'),
                messageType=item.get('messageType', 'text')
            ))
        
        return summaries
    except Exception as e:
        logger.error(f"Error getting summaries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=ConversationStats)
async def get_conversation_stats(
    admin_user: str = Depends(require_admin_role)  # Admin authentication required
):
    """Get conversation statistics (admin only) - basic stats from raw logs"""
    if not conversations_table:
        raise HTTPException(status_code=500, detail="Conversation logs table not configured")
    
    try:
        # Scan all conversations (may be expensive, consider caching)
        response = conversations_table.scan()
        items = response.get('Items', [])
        
        # Calculate basic stats
        total = len(items)
        by_date = {}
        
        # Category and topics stats only available if Step 2.2 (summarization) is implemented
        by_category = {}
        topics_count = {}
        
        for item in items:
            # Date stats (always available)
            date = item['timestamp'][:10]  # YYYY-MM-DD
            by_date[date] = by_date.get(date, 0) + 1
            
            # Category and topics (only if summaries exist)
            summary = item.get('summary')
            if summary:
                category = summary.get('category', 'general')
                by_category[category] = by_category.get(category, 0) + 1
                
                topics = summary.get('topics', [])
                for topic in topics:
                    topics_count[topic] = topics_count.get(topic, 0) + 1
        
        top_topics = sorted(
            [{'topic': k, 'count': v} for k, v in topics_count.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10] if topics_count else []
        
        return ConversationStats(
            total_conversations=total,
            conversations_by_category=by_category if by_category else {},  # Empty if no summaries
            conversations_by_date=by_date,
            top_topics=top_topics
        )
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

