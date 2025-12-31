import google.generativeai as genai
import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from google.protobuf.json_format import MessageToDict
from google.generativeai.types import FunctionDeclaration

# Load .env file for local development
load_dotenv()

logger = logging.getLogger(__name__)

# Import system instruction
try:
    # Try relative import first (from integrations/ to prompts/)
    from ..prompts.system_instruction import get_system_instruction, SYSTEM_INSTRUCTION
except ImportError:
    try:
        # Try absolute import (if PYTHONPATH includes app/api/v1/chat)
        from prompts.system_instruction import get_system_instruction, SYSTEM_INSTRUCTION
    except ImportError:
        try:
            # Try from app.api.v1.chat.prompts
            from app.api.v1.chat.prompts.system_instruction import get_system_instruction, SYSTEM_INSTRUCTION
        except ImportError:
            # Ultimate fallback - use minimal instruction
            logger.warning("Could not import get_system_instruction, using fallback")
            def get_system_instruction(lang: str = "ja") -> str:
                return """You are a chatbot for nihongo.cloud, a Japanese learning app. Answer user questions politely and helpfully. Do not include any links or URLs in your responses."""
            SYSTEM_INSTRUCTION = get_system_instruction("ja")

class GeminiClient:
    def __init__(self):
        api_key = self._get_api_key()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.tools = {}  # Will be populated with tool definitions
    
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
    
    def register_tools(self, tool_functions: Dict[str, Any]):
        """
        Register tool functions with Gemini
        
        Args:
            tool_functions: Dictionary of tool function definitions
        """
        # Store tool functions for execution
        self.tools = tool_functions
        
        # Convert tool functions to Gemini format using protobuf
        # Note: FunctionDeclaration.from_function requires Pydantic models, so we use manual creation
        function_declarations = []
        
        for tool_name, tool_def in tool_functions.items():
            tool_description = tool_def["description"]
            
            # Create function declaration using protobuf
            func_decl = genai.protos.FunctionDeclaration(
                name=tool_name,
                description=tool_description
            )
            
            # Set parameters schema
            schema = genai.protos.Schema(type_=genai.protos.Type.OBJECT)
            
            # Get properties from tool definition
            properties = tool_def["parameters"].get("properties", {})
            
            # Set each property in the schema
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "string")
                
                # Map JSON schema types to protobuf types
                if prop_type == "string":
                    schema_type = genai.protos.Type.STRING
                elif prop_type == "integer":
                    schema_type = genai.protos.Type.INTEGER
                elif prop_type == "number":
                    schema_type = genai.protos.Type.NUMBER
                elif prop_type == "boolean":
                    schema_type = genai.protos.Type.BOOLEAN
                else:
                    schema_type = genai.protos.Type.STRING
                
                # Create property schema
                prop_schema = genai.protos.Schema(
                    type_=schema_type,
                    description=prop_info.get("description", "")
                )
                
                # IMPORTANT: Set the property in the map using proper protobuf map assignment
                # protobuf maps require setting the value directly, not using CopyFrom on a non-existent key
                schema.properties[prop_name] = prop_schema
            
            # Set required fields
            required_fields = tool_def["parameters"].get("required", [])
            if required_fields:
                schema.required.extend(required_fields)
            
            # Set the parameters schema on the function declaration
            # parameters is a Schema field, so we assign the schema directly
            func_decl.parameters = schema
            function_declarations.append(func_decl)
            
            logger.debug(f"Registered tool {tool_name} with {len(properties)} properties")
        
        # Create tools configuration
        if function_declarations:
            tools = [genai.protos.Tool(function_declarations=function_declarations)]
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                tools=tools
            )
        
        logger.info(f"Registered {len(tool_functions)} tools with Gemini")
    
    def chat_with_tools(
        self,
        message: str,
        conversation_history: Optional[List] = None,
        tool_functions: Optional[Dict[str, Any]] = None,
        lang: str = "ja"
    ) -> Dict[str, Any]:
        """
        Send message to Gemini API with tool calling support
        
        Args:
            message: User's message
            conversation_history: Optional list of previous messages
            tool_functions: Optional tool functions to register
            lang: Language code for response (e.g., "ja", "en", "vi", "zh", "ko", "id", "hi"). Defaults to "ja"
        
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
            
            # Start chat session with automatic function calling enabled
            # Use system instruction from prompts/system_instruction.py
            # This includes app information and guidelines for answering various types of questions
            # Customize system instruction based on language
            system_instruction = get_system_instruction(lang)
            
            if conversation_history:
                logger.info(f"Starting chat with conversation history: {len(conversation_history)} messages")
                logger.debug(f"History format sample (first 2 messages): {conversation_history[:2] if len(conversation_history) >= 2 else conversation_history}")
                chat = self.model.start_chat(history=conversation_history)
            else:
                logger.info("Starting chat without conversation history")
                chat = self.model.start_chat()
            
            # Enable automatic function calling if tools are registered
            # This allows Gemini to automatically call tools when needed
            if self.tools:
                logger.info(f"Sending message with {len(self.tools)} tools available")
            
            # Send message with system instruction prepended
            # Combine system instruction with user message
            full_message = f"{system_instruction}\n\nUser question: {message}"
            logger.debug(f"Sending message to Gemini (length: {len(full_message)} chars)")
            response = chat.send_message(full_message)
            
            logger.info(f"Response received, checking for function calls...")
            
            # Check if response requires function calls
            tool_calls = []
            tool_results = []
            
            # Process response for function calls
            # Check if response contains function calls
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check for function calls in content parts
                if hasattr(candidate, 'content') and candidate.content:
                    parts = candidate.content.parts
                    
                    for part in parts:
                        # Check for function_call attribute
                        if hasattr(part, 'function_call') and part.function_call:
                            func_call = part.function_call
                            
                            # Extract function name
                            func_name = func_call.name if hasattr(func_call, 'name') else None
                            
                            if not func_name:
                                continue
                            
                            # Convert function_call.args to dict
                            args = {}
                            if hasattr(func_call, 'args'):
                                func_args = func_call.args
                                
                                # Try different ways to extract args
                                if isinstance(func_args, dict):
                                    args = func_args
                                elif hasattr(func_args, 'fields'):
                                    # Protobuf Struct type - convert fields to dict
                                    try:
                                        # Method 1: Use MessageToDict (most reliable)
                                        args = MessageToDict(func_args)
                                    except Exception as e1:
                                        logger.warning(f"MessageToDict failed: {e1}")
                                        try:
                                            # Method 2: Direct access to fields (protobuf Struct)
                                            # Struct.fields is a dict-like object
                                            if hasattr(func_args.fields, 'items'):
                                                for key, value in func_args.fields.items():
                                                    # Convert protobuf Value to Python type
                                                    if hasattr(value, 'string_value'):
                                                        args[key] = value.string_value
                                                    elif hasattr(value, 'number_value'):
                                                        args[key] = value.number_value
                                                    elif hasattr(value, 'bool_value'):
                                                        args[key] = value.bool_value
                                                    else:
                                                        args[key] = str(value)
                                        except Exception as e2:
                                            logger.warning(f"Direct fields access failed: {e2}")
                                            # Method 3: Try MessageToDict on the whole function_call
                                            try:
                                                full_dict = MessageToDict(func_call)
                                                args = full_dict.get('args', {})
                                            except Exception as e3:
                                                logger.error(f"All conversion methods failed: {e3}")
                                elif hasattr(func_args, 'items'):
                                    args = dict(func_args.items())
                                elif hasattr(func_args, 'DESCRIPTOR'):
                                    # Protobuf message - convert to dict
                                    try:
                                        args = MessageToDict(func_args)
                                    except Exception as e:
                                        logger.warning(f"Failed to convert args using MessageToDict: {e}")
                                        # Fallback: manual extraction
                                        for field in func_args.DESCRIPTOR.fields:
                                            field_value = getattr(func_args, field.name, None)
                                            if field_value is not None:
                                                args[field.name] = field_value
                            
                            # Log args for debugging
                            logger.info(f"Function call: {func_name}, args: {args}, args_type: {type(func_call.args) if hasattr(func_call, 'args') else 'N/A'}")
                            
                            # Validate args are not empty
                            if not args:
                                logger.warning(f"Empty args for function {func_name}")
                                if hasattr(func_call, 'args'):
                                    logger.warning(f"function_call.args type: {type(func_call.args)}")
                                    logger.warning(f"function_call.args repr: {repr(func_call.args)}")
                                    if hasattr(func_call.args, 'fields'):
                                        logger.warning(f"function_call.args.fields: {func_call.args.fields}")
                            
                            tool_calls.append({
                                "name": func_name,
                                "args": args
                            })
                            
                            # Execute function call
                            if self.tools and func_name in self.tools:
                                tool_func = self.tools[func_name]["function"]
                                
                                try:
                                    # Validate required arguments
                                    if not args:
                                        error_msg = f"Function {func_name} requires arguments but none were provided"
                                        logger.error(error_msg)
                                        raise ValueError(error_msg)
                                    
                                    result = tool_func(**args)
                                    tool_results.append({
                                        "name": func_name,
                                        "result": result
                                    })
                                    
                                    # Create function response for Gemini using protobuf
                                    function_response_part = genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=func_name,
                                            response=result
                                        )
                                    )
                                    function_response = chat.send_message([function_response_part])
                                    
                                    # Get final response after tool call
                                    response = function_response
                                
                                except TypeError as e:
                                    # This usually means missing required arguments
                                    error_msg = f"Function {func_name} missing required arguments. Provided: {args}, Error: {str(e)}"
                                    logger.error(error_msg)
                                    tool_results.append({
                                        "name": func_name,
                                        "error": error_msg
                                    })
                                    # Continue without tool result - let Gemini handle it
                                except Exception as e:
                                    error_msg = f"Error executing tool {func_name}: {str(e)}"
                                    logger.error(error_msg)
                                    tool_results.append({
                                        "name": func_name,
                                        "error": error_msg
                                    })
            
            # Extract response text
            # If there are function calls, we need to handle the response differently
            # The response might contain function_call parts that can't be converted to text directly
            try:
                response_text = response.text
            except ValueError as e:
                # If response contains function_call parts, try to get text from parts
                if "function_call" in str(e):
                    logger.warning("Response contains function_call parts, extracting text from parts")
                    text_parts = []
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                                elif hasattr(part, 'function_call'):
                                    # Function call part - skip or log
                                    logger.debug(f"Skipping function_call part: {part.function_call.name if hasattr(part.function_call, 'name') else 'unknown'}")
                    
                    if text_parts:
                        response_text = " ".join(text_parts)
                    else:
                        # If no text parts found, use a default message
                        response_text = "I processed your request, but I need more information to provide a complete answer."
                        logger.warning("No text parts found in response with function calls")
                else:
                    # Re-raise if it's a different error
                    raise
            
            return {
                "response": response_text,
                "tool_calls": tool_calls,
                "tool_results": tool_results
            }
        
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
    
    def chat(self, message: str, conversation_history: Optional[list] = None) -> str:
        """
        Simple chat without tools (backward compatibility)
        
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

