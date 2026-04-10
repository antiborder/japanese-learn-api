from google import genai
from google.genai import types
import os
import logging
import re
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

logger = logging.getLogger(__name__)

# Import system instruction
try:
    from ..prompts.system_instruction import get_system_instruction, SYSTEM_INSTRUCTION
except ImportError:
    try:
        from prompts.system_instruction import get_system_instruction, SYSTEM_INSTRUCTION
    except ImportError:
        try:
            from app.api.v1.chat.prompts.system_instruction import get_system_instruction, SYSTEM_INSTRUCTION
        except ImportError:
            logger.warning("Could not import get_system_instruction, using fallback")
            def get_system_instruction(lang: str = "ja") -> str:
                return "You are a chatbot for nihongo.cloud, a Japanese learning app. Answer user questions politely and helpfully. Do not include any links or URLs in your responses."
            SYSTEM_INSTRUCTION = get_system_instruction("ja")

MODEL_NAME = 'gemini-3.1-flash-lite-preview'

# JSON schema type -> google.genai types.Type mapping
_TYPE_MAP = {
    "string": types.Type.STRING,
    "integer": types.Type.INTEGER,
    "number": types.Type.NUMBER,
    "boolean": types.Type.BOOLEAN,
}


class GeminiClient:
    def __init__(self):
        api_key = self._get_api_key()
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha'),
        )
        self.tools: Dict[str, Any] = {}
        self._gemini_tools: Optional[List[types.Tool]] = None

    def _get_api_key(self) -> str:
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            logger.info("Using GEMINI_API_KEY from environment variable")
            return api_key
        try:
            import boto3
            secrets_client = boto3.client('secretsmanager')
            secret_name = os.getenv('GEMINI_API_KEY_SECRET_NAME', 'gemini-api-key')
            secret = secrets_client.get_secret_value(SecretId=secret_name)
            logger.info("Using GEMINI_API_KEY from Secrets Manager")
            return secret['SecretString']
        except Exception as e:
            logger.warning(f"Could not get API key from Secrets Manager: {e}")
            raise ValueError("GEMINI_API_KEY not found in environment or Secrets Manager")

    def register_tools(self, tool_functions: Dict[str, Any]):
        self.tools = tool_functions

        function_declarations = []
        for tool_name, tool_def in tool_functions.items():
            properties = {}
            for prop_name, prop_info in tool_def["parameters"].get("properties", {}).items():
                prop_type = prop_info.get("type", "string")
                properties[prop_name] = types.Schema(
                    type=_TYPE_MAP.get(prop_type, types.Type.STRING),
                    description=prop_info.get("description", "")
                )

            required_fields = tool_def["parameters"].get("required", [])
            func_decl = types.FunctionDeclaration(
                name=tool_name,
                description=tool_def["description"],
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=properties,
                    required=required_fields if required_fields else None
                )
            )
            function_declarations.append(func_decl)
            logger.debug(f"Registered tool {tool_name} with {len(properties)} properties")

        self._gemini_tools = [types.Tool(function_declarations=function_declarations)]
        logger.info(f"Registered {len(tool_functions)} tools")

    def _make_config(self, system_instruction: str) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=self._gemini_tools if self._gemini_tools else None,
        )

    def _convert_history(self, history: List[Dict]) -> List[types.Content]:
        """Convert dict-format history to types.Content list."""
        result = []
        for msg in history:
            role = msg.get("role", "user")
            parts = []
            for p in msg.get("parts", []):
                if isinstance(p, dict) and "text" in p:
                    parts.append(types.Part(text=p["text"]))
                elif isinstance(p, str):
                    parts.append(types.Part(text=p))
            if parts:
                result.append(types.Content(role=role, parts=parts))
        return result

    def _extract_text(self, response) -> str:
        try:
            return response.text
        except Exception:
            text_parts = []
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
            if text_parts:
                return " ".join(text_parts)
            logger.warning("No text parts found in response")
            return "I processed your request, but I need more information to provide a complete answer."

    def chat_with_tools_iterative(
        self,
        message: str,
        conversation_history: Optional[List] = None,
        tool_functions: Optional[Dict[str, Any]] = None,
        max_iterations: int = 5,
        lang: str = "ja"
    ) -> Dict[str, Any]:
        """
        Chat with iterative tool calling (multi-step tool chaining).
        Authentication: Required — caller must ensure user is authenticated.
        """
        try:
            if tool_functions:
                self.register_tools(tool_functions)

            system_instruction = get_system_instruction(lang)
            history = self._convert_history(conversation_history) if conversation_history else []

            chat = self.client.chats.create(
                model=MODEL_NAME,
                config=self._make_config(system_instruction),
                history=history,
            )

            logger.info(f"Starting iterative chat (history={len(history)}, tools={len(self.tools)}, max_iterations={max_iterations})")
            response = chat.send_message(message)

            iteration = 0
            all_tool_calls: List[Dict] = []
            all_tool_results: List[Dict] = []

            while iteration < max_iterations:
                function_calls_found = False

                if not response.candidates:
                    break

                for part in response.candidates[0].content.parts:
                    if not part.function_call:
                        continue

                    function_calls_found = True
                    func_name = part.function_call.name
                    args = dict(part.function_call.args) if part.function_call.args else {}

                    if func_name not in self.tools:
                        logger.warning(f"Unknown function call: {func_name}")
                        continue

                    logger.info(f"Iteration {iteration + 1}: Calling {func_name} with args: {args}")

                    try:
                        if not args:
                            raise ValueError(f"Function {func_name} requires arguments but none were provided")

                        result = self.tools[func_name]["function"](**args)
                        all_tool_calls.append({"name": func_name, "args": args})
                        all_tool_results.append({"name": func_name, "result": result})

                        logger.info(f"Iteration {iteration + 1}: {func_name} completed")

                        response = chat.send_message(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=func_name,
                                    response=result if isinstance(result, dict) else {"result": result}
                                )
                            )
                        )
                        iteration += 1
                        break

                    except Exception as e:
                        error_msg = f"Error executing tool {func_name}: {str(e)}"
                        logger.error(error_msg)
                        all_tool_results.append({"name": func_name, "error": error_msg})
                        break

                if not function_calls_found:
                    logger.info(f"No more tool calls after {iteration} iterations")
                    break

            return {
                "response": self._extract_text(response),
                "tool_calls": all_tool_calls,
                "tool_results": all_tool_results,
                "iterations": iteration,
            }

        except Exception as e:
            logger.error(f"Error in iterative tool calling: {str(e)}")
            raise

    def chat_with_tools(
        self,
        message: str,
        conversation_history: Optional[List] = None,
        tool_functions: Optional[Dict[str, Any]] = None,
        lang: str = "ja"
    ) -> Dict[str, Any]:
        """Single-step tool calling (delegates to iterative with max_iterations=1)."""
        return self.chat_with_tools_iterative(
            message,
            conversation_history=conversation_history,
            tool_functions=tool_functions,
            max_iterations=1,
            lang=lang,
        )

    def generate_word_variations(
        self,
        word_name: str,
        lang: str = "ja",
        max_variations: int = 10
    ) -> Dict[str, Any]:
        """Generate word variations (conjugations, writing forms, politeness levels)."""
        try:
            prompt = f"""You are a Japanese language expert. Generate word variations for: {word_name}

Generate variations including:
1. **Writing variations (kanji ↔ hiragana ↔ katakana)**
   - Example: 「いぬ」→「犬」, 「嬉しい」→「うれしい」
   - If natural, convert hiragana to kanji, or kanji to hiragana

2. **Verb conjugation forms (ます形, 過去形, て形, 否定形)**
   - **CRITICAL: For verbs, ALWAYS include ます形 (masu form)**
   - Example: 「戦う」→「戦います」 (must include ます形)
   - This app stores verbs in ます形 format

3. **Adjectival noun (形容動詞) conjugation forms**
   - **CRITICAL: For 形容動詞, ALWAYS include 連体形 (attributive form ending with "な")**
   - Example: 「静かだ」→「静かな」 (must include 連体形)
   - This app stores 形容動詞 in 連体形 format

4. **Adjective (形容詞) conjugation forms**
   - **CRITICAL: For 形容詞, ALWAYS include 終止形 (predicative form ending with "い")**
   - Example: 「楽し」→「楽しい」 (must include 終止形)
   - This app stores 形容詞 in 終止形 format

5. **Part-of-speech variations**
   - Example: 「素早く」(adverb) → 「素早い」(noun), 「扱い」(noun) → 「扱います」(verb)

6. **Politeness/honorific variations**
   - Example: 「菓子」→「お菓子」, 「お見積もり」→「見積もり」

**CRITICAL: Return ONLY clean Japanese words (kanji, hiragana, or katakana)**
- Do NOT include romanization (romaji) like (kariru) or (karimasu)
- Do NOT include annotations, descriptions, or grammatical labels like [Dictionary form] or [ます形]
- Do NOT include explanations, parentheses, or brackets
- Return ONLY the pure Japanese text: 借りる, 借ります, 借りた, etc.

Examples:
- CORRECT: "借ります"
- WRONG: "借ります (karimasu)"
- WRONG: "借ります [ます形]"
- WRONG: "借ります (karimasu) - ます形"

Return ONLY a JSON object:
{{
    "variations": ["variation1", "variation2", ...],
    "reasoning": "Brief explanation",
    "confidence": 0.0-1.0
}}

Generate {max_variations} variations (7-10 variations).
Prioritize common forms (ます形 for verbs, dictionary form, 連体形 for 形容動詞, 終止形 for 形容詞).
Include both kanji and hiragana versions if applicable.
Focus on forms that might exist in a Japanese learning database.
Each variation must be a clean Japanese word only, no annotations.
"""
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            result = self._parse_variation_response(response.text)

            if len(result.get("variations", [])) > max_variations:
                result["variations"] = result["variations"][:max_variations]

            logger.info(f"Generated {len(result.get('variations', []))} variations for '{word_name}'")
            return result

        except Exception as e:
            logger.error(f"Error generating word variations for '{word_name}': {str(e)}")
            return {"variations": [], "reasoning": f"Error: {str(e)}", "confidence": 0.0}

    def _parse_variation_response(self, response_text: str) -> Dict[str, Any]:
        json_match = re.search(r'\{[^{}]*"variations"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            json_str = json_match.group(0) if json_match else response_text.strip()

        try:
            result = json.loads(json_str)
            result.setdefault("variations", [])
            result.setdefault("reasoning", "Generated variations")
            result.setdefault("confidence", 0.5)

            if not isinstance(result["variations"], list):
                result["variations"] = []

            try:
                result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
            except (ValueError, TypeError):
                result["confidence"] = 0.5

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}, response: {response_text[:200]}")
            words = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+', response_text)
            seen: set = set()
            unique_words = []
            for word in words:
                if word not in seen and len(word) > 0:
                    seen.add(word)
                    unique_words.append(word)
            return {
                "variations": unique_words[:10],
                "reasoning": "Extracted from text (JSON parse failed)",
                "confidence": 0.3,
            }

    def chat(self, message: str, conversation_history: Optional[list] = None) -> str:
        """Simple chat without tools (backward compatibility)."""
        try:
            history = self._convert_history(conversation_history) if conversation_history else []
            chat = self.client.chats.create(model=MODEL_NAME, history=history)
            response = chat.send_message(message)
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
