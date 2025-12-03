import google.generativeai as genai
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        api_key = self._get_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def _get_api_key(self) -> str:
        """Get Gemini API key from environment variable or Secrets Manager"""
        # First, try environment variable (matches pattern used by other functions)
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            logger.info("Using GEMINI_API_KEY from environment variable")
            return api_key
        
        # Fallback to Secrets Manager (for future use or if env var not set)
        try:
            import boto3
            secrets_client = boto3.client('secretsmanager')
            secret_name = os.getenv('GEMINI_API_KEY_SECRET_NAME', 'gemini-api-key')
            secret = secrets_client.get_secret_value(SecretId=secret_name)
            logger.info("Using GEMINI_API_KEY from Secrets Manager")
            return secret['SecretString']
        except Exception as e:
            logger.warning(f"Could not get API key from Secrets Manager: {e}")
            # If both fail, raise error
            raise ValueError("GEMINI_API_KEY not found in environment or Secrets Manager")
    
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

