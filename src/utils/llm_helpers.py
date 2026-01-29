from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import settings
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
from openai import OpenAI

logger = logging.getLogger(__name__)

# OpenAI client for Whisper API (singleton)
_openai_client = None

def get_openai_client():
    """Get singleton OpenAI client"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
    return _openai_client

# Backwards compatible alias - use get_openai_client() for new code
client = None  # Will be lazily initialized

def _get_client():
    """Lazy initialization for backwards compatibility"""
    global client
    if client is None:
        client = get_openai_client()
    return client

# Circuit breaker pattern for LLM resilience
class CircuitBreaker:
    """Circuit breaker to prevent cascading failures"""
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half_open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise Exception("Circuit breaker is OPEN - LLM service unavailable")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failures = 0
                logger.info("Circuit breaker closed - service recovered")
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.utcnow()
            if self.failures >= self.failure_threshold:
                self.state = "open"
                logger.error(f"Circuit breaker OPENED after {self.failures} failures")
            raise e

# Global circuit breaker instance
circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

# Create LangChain ChatOpenAI client - automatically integrates with LangSmith
chat_model = ChatOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    model=settings.llm_model,
    temperature=0.7,
    timeout=settings.request_timeout,
    max_retries=0  # We handle retries manually for better control
)

def convert_to_langchain_messages(messages: list) -> List:
    """Convert OpenAI-style messages to LangChain message objects with validation"""
    if not messages:
        raise ValueError("Messages list cannot be empty")
    
    langchain_messages = []
    for msg in messages:
        if not isinstance(msg, dict):
            logger.warning(f"Skipping invalid message format: {msg}")
            continue
            
        role = msg.get("role")
        content = msg.get("content")
        
        if not content:
            logger.warning(f"Skipping message with empty content: {msg}")
            continue
        
        if role == "system":
            langchain_messages.append(SystemMessage(content=content))
        elif role == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_messages.append(AIMessage(content=content))
        else:
            logger.warning(f"Unknown role '{role}', treating as user message")
            langchain_messages.append(HumanMessage(content=content))
    
    if not langchain_messages:
        raise ValueError("No valid messages after conversion")
    
    return langchain_messages

def call_llm_with_retry(
    messages: list, 
    max_retries: int = 3, 
    temperature: float = 0.7, 
    run_name: Optional[str] = None,
    fallback_response: Optional[str] = None
) -> Dict[Any, Any]:
    """Call LLM with comprehensive error handling, retry logic, and circuit breaker
    
    Args:
        messages: List of message dictionaries
        max_retries: Maximum retry attempts (default: 3)
        temperature: LLM temperature (default: 0.7)
        run_name: Name for LangSmith tracing
        fallback_response: Response to return if all retries fail
    
    Returns:
        Dict with 'content' and 'role' keys
    
    Raises:
        Exception: If all retries fail and no fallback provided
    """
    if not messages:
        logger.error("Empty messages list provided to LLM")
        if fallback_response:
            return {"content": fallback_response, "role": "assistant"}
        raise ValueError("Messages list cannot be empty")
    
    # Validate and convert messages
    try:
        langchain_messages = convert_to_langchain_messages(messages)
    except ValueError as e:
        logger.error(f"Message conversion failed: {e}")
        if fallback_response:
            return {"content": fallback_response, "role": "assistant"}
        raise
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Use circuit breaker pattern
            response = circuit_breaker.call(
                chat_model.invoke,
                langchain_messages,
                config={
                    "run_name": run_name or "llm_call", 
                    "temperature": temperature,
                    "tags": [f"attempt_{attempt + 1}", "multi_agent_system"]
                }
            )
            
            # Validate response
            if not response or not hasattr(response, 'content'):
                raise ValueError("Invalid response from LLM")
            
            if not response.content or not response.content.strip():
                raise ValueError("Empty response from LLM")
            
            logger.info(f"LLM call successful on attempt {attempt + 1}")
            return {
                "content": response.content,
                "role": "assistant"
            }
            
        except Exception as e:
            last_error = e
            error_type = type(e).__name__
            logger.warning(
                f"LLM call failed on attempt {attempt + 1}/{max_retries}: {error_type} - {str(e)}"
            )
            
            # Don't retry on certain errors
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                logger.error("Authentication error - not retrying")
                break
            
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                sleep_time = (2 ** attempt) + (time.time() % 1)  # Add jitter
                logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
    
    # All retries failed
    logger.error(f"LLM call failed after {max_retries} attempts. Last error: {last_error}")
    
    if fallback_response:
        logger.info("Returning fallback response")
        return {"content": fallback_response, "role": "assistant"}
    
    raise Exception(
        f"LLM call failed after {max_retries} attempts: {str(last_error)}"
    )
