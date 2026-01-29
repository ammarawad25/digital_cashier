from sqlalchemy.orm import Session
from src.models.schemas import IntentResult
from src.models.enums import IntentType, Sentiment
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import settings
import json
import re
import logging

logger = logging.getLogger(__name__)

# Singleton LLM instances for intent detection - avoid re-initialization
_fast_llm_instance = None
_standard_llm_instance = None

def _get_fast_llm():
    """Get singleton fast LLM for intent detection with fallback"""
    global _fast_llm_instance
    if _fast_llm_instance is None:
        # Try fast model first, fallback to main model if not available
        model = settings.llm_model_fast if settings.use_fast_model_for_intent else settings.llm_model
        logger.info(f"Initializing intent detection LLM: {model}")
        try:
            _fast_llm_instance = ChatOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=model,
                temperature=0.1,  # Minimal for fastest, most deterministic responses
                timeout=5,  # Aggressive timeout for classification
                max_tokens=200,  # Strict limit for speed
                streaming=True  # Enable streaming for faster initial response
            )
        except Exception as e:
            # Fallback to main model
            logger.warning(f"Fast model {model} not available, falling back to {settings.llm_model}: {e}")
            _fast_llm_instance = ChatOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.llm_model,
                temperature=0.1,
                timeout=5,
                max_tokens=200,
                streaming=True
            )
    return _fast_llm_instance


class IntentDetection:
    def __init__(self, db: Session):
        self.db = db
        # Use singleton fast LLM for intent detection
        self.llm = _get_fast_llm()
        
    def detect(self, message: str, conversation_history: list = None, session_context: dict = None) -> IntentResult:
        """Detect intent with context-aware reasoning
        
        Args:
            message: User's message
            conversation_history: Previous messages
            session_context: Current session state (order_draft, conversation_state, etc.)
        
        Returns:
            IntentResult with intent, confidence, entities, and sentiment
        """
        if not message or not message.strip():
            logger.warning("Empty message provided to intent detection")
            return IntentResult(
                intent=IntentType.UNCLEAR,
                confidence=0.0,
                entities={},
                sentiment=Sentiment.NEUTRAL
            )
        
        # Build context-aware prompt
        context_info = ""
        if session_context:
            has_order = bool(session_context.get("has_order_draft"))
            order_items_count = session_context.get("order_items_count", 0)
            conv_state = session_context.get("conversation_state", "unknown")
            
            context_info = f"\n\nCONTEXT: order_exists={has_order}, items={order_items_count}, state={conv_state}"
        
        # OPTIMIZED: Ultra-compact prompt for fastest inference
        system_prompt = f"""Intent classifier. Return JSON ONLY.

INTENTS:
ordering: "أريد/want/بدي" + food OR "نعم" + food names
remove: "احذف/remove/delete" item
confirm_order: "تم/نعم/ok/confirm" (no food + order exists)
cancel: "إلغاء/ألغي/cancel/new order/طلب جديد/من جديد/start over/clear"
escalate: "موظف/agent/تحويل"
inquiry: questions (menu/price/location)
tracking: "وين طلبي/where order"
complaint: problem + negative
greeting: "مرحبا/hello"
farewell: "شكرا/bye"

CONTEXT: If "yes/نعم" + food names → ordering. If "yes/نعم" + order exists → confirm_order{context_info}

ENTITIES: Extract items as [{{"name":"X","quantity":N}}]. Arabic: واحد=1, اثنين=2, ثلاثة=3

FORMAT: {{"intent":"X","confidence":0.9,"sentiment":"neutral","entities":{{}}}}"""
        
        # Simplified context handling - only use message without complex history
        prompt_messages = [SystemMessage(content=system_prompt)]
        
        # Only add conversation context if really needed (optimize for speed)
        if conversation_history and len(conversation_history) > 1:
            # Only last user message for minimal context
            last_user_msg = None
            for msg in reversed(conversation_history[-2:]):  # Only check last 2
                if msg.get("role") == "user" and msg.get("content"):
                    last_user_msg = msg.get("content")[:150]  # Further truncate
                    break
            if last_user_msg and last_user_msg != message:
                prompt_messages.append(HumanMessage(content=f"Previous: {last_user_msg}"))
        
        prompt_messages.append(HumanMessage(content=f"Classify: {message}"))
        
        try:
            response = self.llm.invoke(prompt_messages)
            
            if not response or not response.content:
                logger.error("Empty response from LLM in intent detection")
                return IntentResult(
                    intent=IntentType.UNCLEAR,
                    confidence=0.2,
                    entities={},
                    sentiment=Sentiment.NEUTRAL
                )
            
            result = self._parse_response(response.content, message)
            
            # Validate result
            if not self._validate_intent_result(result):
                logger.warning(f"Invalid intent result, using fallback: {result}")
                return IntentResult(
                    intent=IntentType.UNCLEAR,
                    confidence=0.2,
                    entities={},
                    sentiment=Sentiment.NEUTRAL
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return IntentResult(
                intent=IntentType.UNCLEAR,
                confidence=0.1,
                entities={},
                sentiment=Sentiment.NEUTRAL
            )
    
    def _parse_response(self, response: str, original_message: str = "") -> IntentResult:
        """Parse LLM response with enhanced error handling and validation"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            # Validate and extract fields with defaults
            intent_str = data.get("intent", "unclear")
            try:
                intent = IntentType(intent_str)
            except ValueError:
                logger.warning(f"Invalid intent type '{intent_str}', defaulting to UNCLEAR")
                intent = IntentType.UNCLEAR
            
            confidence = float(data.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            sentiment_str = data.get("sentiment", "neutral")
            try:
                sentiment = Sentiment(sentiment_str)
            except ValueError:
                logger.warning(f"Invalid sentiment '{sentiment_str}', defaulting to NEUTRAL")
                sentiment = Sentiment.NEUTRAL
            
            entities = data.get("entities", {})
            # Handle entities as either dict or list of items
            if isinstance(entities, list):
                # Convert list of items to dict format
                entities = {"items": entities}
            elif not isinstance(entities, dict):
                logger.warning(f"Invalid entities format: {entities}")
                entities = {}
            
            return IntentResult(
                intent=intent,
                confidence=confidence,
                entities=entities,
                sentiment=sentiment
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}. Response: {response[:200]}")
            return IntentResult(
                intent=IntentType.UNCLEAR,
                confidence=0.2,
                entities={},
                sentiment=Sentiment.NEUTRAL
            )
        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
            return IntentResult(
                intent=IntentType.UNCLEAR,
                confidence=0.1,
                entities={},
                sentiment=Sentiment.NEUTRAL
            )
    
    def _validate_intent_result(self, result: IntentResult) -> bool:
        """Validate intent result for consistency and completeness"""
        # Check if result has required fields
        if not result or not isinstance(result, IntentResult):
            return False
        
        # Check confidence bounds
        if result.confidence < 0.0 or result.confidence > 1.0:
            logger.warning(f"Confidence out of bounds: {result.confidence}")
            return False
        
        # Validate intent-specific requirements
        if result.intent == IntentType.ORDERING:
            entities = result.entities
            if not entities.get("items"):
                logger.warning("ORDERING intent without items entities")
                # This is acceptable - might be clarification needed
        
        return True
