import boto3
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ConversationLogger:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        table_name = os.getenv('CONVERSATION_LOGS_TABLE_NAME')
        if not table_name:
            logger.warning("CONVERSATION_LOGS_TABLE_NAME not set, logging will be disabled")
            self.table = None
        else:
            self.table = self.dynamodb.Table(table_name)
    
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
            user_id: User ID from authentication (or anonymous-{session_id})
            session_id: Session ID for conversation continuity
            question: User's question
            response: Chatbot's response
            message_type: "text" or "voice"
            metadata: Optional additional metadata
        """
        if not self.table:
            logger.debug("Conversation logging disabled (table not configured)")
            return
        
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

