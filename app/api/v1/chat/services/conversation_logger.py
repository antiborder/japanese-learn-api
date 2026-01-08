import boto3
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class ConversationLogger:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        table_name = os.getenv('CONVERSATION_LOGS_TABLE_NAME')
        logger.info(f"[CONV_LOGGER_INIT] CONVERSATION_LOGS_TABLE_NAME env var: '{table_name}'")
        if not table_name:
            logger.warning("[CONV_LOGGER_INIT] CONVERSATION_LOGS_TABLE_NAME not set, logging will be disabled")
            self.table = None
        else:
            logger.info(f"[CONV_LOGGER_INIT] Initializing table: {table_name}")
            self.table = self.dynamodb.Table(table_name)
            logger.info(f"[CONV_LOGGER_INIT] Table initialized: {self.table is not None}")
    
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
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> Optional[List[Dict]]:
        """
        Retrieve conversation history for a session from DynamoDB
        
        Args:
            session_id: Session ID to retrieve history for
            limit: Maximum number of conversation turns to retrieve (default: 20)
        
        Returns:
            List of messages formatted for Gemini chat history, or None if:
            - Table is not configured
            - No history found
            - Error occurred
            
        Format returned:
        [
            {"role": "user", "parts": [{"text": "user question"}]},
            {"role": "model", "parts": [{"text": "bot response"}]},
            ...
        ]
        """
        if not self.table:
            logger.warning(f"[CONV_LOGGER] Conversation logging disabled (table not configured), cannot retrieve history. self.table={self.table}")
            return None
        
        logger.info(f"[CONV_LOGGER] Table is configured, querying for session {session_id}")
        
        try:
            # Query DynamoDB for all messages in this session
            # sessionId is the partition key, timestamp is the sort key
            # Each DynamoDB item represents one conversation turn (question + response)
            # So we query for 'limit' items, which will become limit*2 messages in history
            response = self.table.query(
                KeyConditionExpression="sessionId = :sid",
                ExpressionAttributeValues={
                    ":sid": session_id
                },
                ScanIndexForward=True,  # Sort by timestamp ascending (oldest first)
                Limit=limit  # Number of conversation turns to retrieve
            )
            
            items = response.get('Items', [])
            
            if not items:
                logger.debug(f"No conversation history found for session {session_id}")
                return None
            
            # Sort by timestamp to ensure chronological order
            items.sort(key=lambda x: x.get('timestamp', ''))
            
            # Format messages for Gemini chat history
            # Gemini expects: [{"role": "user", "parts": [{"text": "..."}]}, {"role": "model", "parts": [{"text": "..."}]}]
            history = []
            
            for item in items:
                question = item.get('question', '')
                response = item.get('response', '')
                
                # Add user message
                if question:
                    history.append({
                        "role": "user",
                        "parts": [{"text": question}]
                    })
                
                # Add model response
                if response:
                    history.append({
                        "role": "model",
                        "parts": [{"text": response}]
                    })
            
            # Limit to last N turns (each turn = user + model = 2 messages)
            if len(history) > limit * 2:
                history = history[-(limit * 2):]
                logger.info(f"Limited history to last {limit} turns ({len(history)} messages)")
            
            logger.info(f"[CONV_LOGGER] Retrieved {len(history)} messages from conversation history for session {session_id}")
            # Log the structure of the first message to verify format
            if history and len(history) > 0:
                logger.info(f"[CONV_LOGGER] History format check - first message keys: {list(history[0].keys())}, has 'role': {'role' in history[0]}, has 'parts': {'parts' in history[0]}")
                logger.info(f"[CONV_LOGGER] First message sample: {history[0]}")
                logger.info(f"[CONV_LOGGER] Returning history list with {len(history)} items")
            else:
                logger.warning(f"[CONV_LOGGER] History list is empty even though items were processed")
            
            return history if history else None
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history for session {session_id}: {str(e)}")
            # Don't fail the request if history retrieval fails
            return None

