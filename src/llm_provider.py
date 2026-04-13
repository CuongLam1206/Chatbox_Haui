"""
LLM Provider with automatic fallbacks and retry logic for rate limits
"""
import time
import functools
from typing import Any, Optional, List

from langchain_core.runnables import RunnableSerializable
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from core.config import (
    OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY,
    USE_OLLAMA, USE_GROQ, USE_OPENROUTER, USE_GEMINI,
    OLLAMA_BASE_URL, OLLAMA_MODEL, GROQ_MODEL, OPENROUTER_MODEL, GEMINI_MODEL,
    LLM_MODEL, TEMPERATURE
)

# ── Rate Limit Retry Wrapper ──────────────────────────────────────────────
MAX_RETRIES = 5
BASE_DELAY = 2  # seconds
MAX_DELAY = 30  # seconds


def _is_rate_limit_error(exc):
    """Check if exception is a rate limit (429) error."""
    err_str = str(exc).lower()
    return any(keyword in err_str for keyword in [
        "429", "rate limit", "resource exhausted", "quota",
        "too many requests", "resourceexhausted"
    ])


def _retry_call(method, method_name, max_retries=MAX_RETRIES, base_delay=BASE_DELAY):
    """Create a retry-wrapped version of a callable."""
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                return method(*args, **kwargs)
            except Exception as exc:
                if _is_rate_limit_error(exc):
                    delay = min(base_delay * (2 ** (attempt - 1)), MAX_DELAY)
                    print(f"[LLM Retry] Rate limited on {method_name} "
                          f"(attempt {attempt}/{max_retries}). "
                          f"Waiting {delay}s...")
                    time.sleep(delay)
                    last_exc = exc
                else:
                    raise
        print(f"[LLM Retry] All {max_retries} retries exhausted for {method_name}.")
        raise last_exc
    return wrapper


class RetryLLMWrapper(RunnableSerializable):
    """
    Wraps a LangChain LLM/ChatModel to add automatic retry with exponential
    backoff when rate-limited (HTTP 429).
    Inherits from RunnableSerializable so it works with LangChain's pipe operator.
    """
    llm: Any = None
    max_retries_count: int = MAX_RETRIES
    base_delay_sec: int = BASE_DELAY

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, llm, max_retries=MAX_RETRIES, base_delay=BASE_DELAY, **kwargs):
        super().__init__(llm=llm, max_retries_count=max_retries, base_delay_sec=base_delay, **kwargs)

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs) -> Any:
        return _retry_call(
            self.llm.invoke, "invoke",
            self.max_retries_count, self.base_delay_sec
        )(input, config=config, **kwargs)

    def batch(self, inputs: List[Any], config: Optional[RunnableConfig] = None, **kwargs) -> List[Any]:
        return _retry_call(
            self.llm.batch, "batch",
            self.max_retries_count, self.base_delay_sec
        )(inputs, config=config, **kwargs)

    # -- Proxy all other attributes to the inner LLM --
    def __getattr__(self, name):
        if name in ("llm", "max_retries_count", "base_delay_sec"):
            raise AttributeError(name)
        return getattr(self.llm, name)

    # -- Support with_structured_output for Router/Grader --
    def with_structured_output(self, schema, **kwargs):
        structured = self.llm.with_structured_output(schema, **kwargs)
        return RetryLLMWrapper(structured, self.max_retries_count, self.base_delay_sec)
# ──────────────────────────────────────────────────────────────────────────

# Lazy import for optional providers
def _get_ollama():
    from langchain_ollama import ChatOllama
    return ChatOllama


def get_llm(temperature=TEMPERATURE):
    """
    Get LLM with prioritizes: Gemini -> OpenRouter -> Groq -> OpenAI -> Ollama
    
    Args:
        temperature: Temperature for generation
        
    Returns:
        ChatModel instance
    """
    # 0. Use Gemini if enabled (Highest priority)
    if USE_GEMINI and GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print(f"[LLM] Using Gemini: {GEMINI_MODEL}")
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=temperature,
            google_api_key=GEMINI_API_KEY,
            convert_system_message_to_human=True
        )
        return RetryLLMWrapper(llm)

    # 1. Use OpenRouter if enabled
    if USE_OPENROUTER and OPENROUTER_API_KEY:
        print(f"[LLM] Using OpenRouter: {OPENROUTER_MODEL}")
        return ChatOpenAI(
            model=OPENROUTER_MODEL,
            temperature=temperature,
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )

    # 2. Use Groq if enabled
    if USE_GROQ and GROQ_API_KEY:
        print(f"[LLM] Using Groq: {GROQ_MODEL}")
        return ChatGroq(
            model_name=GROQ_MODEL,
            temperature=temperature,
            groq_api_key=GROQ_API_KEY
        )

    # 3. Use Ollama if explicitly set
    if USE_OLLAMA:
        print(f"[LLM] Using Ollama: {OLLAMA_MODEL}")
        ChatOllama = _get_ollama()
        return ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=temperature
        )
    
    # 4. Try OpenAI
    if OPENAI_API_KEY:
        try:
            llm = ChatOpenAI(
                model=LLM_MODEL,
                temperature=temperature,
                api_key=OPENAI_API_KEY
            )
            print(f"[LLM] Using OpenAI: {LLM_MODEL}")
            return llm
        except Exception as e:
            print(f"[LLM] OpenAI failed: {e}")
            print(f"[LLM] Falling back to Ollama: {OLLAMA_MODEL}")
    else:
        print("[LLM] No API key found or enabled")
        print(f"[LLM] Falling back to Ollama: {OLLAMA_MODEL}")
    
    # Final Fallback to Ollama
    ChatOllama = _get_ollama()
    return ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=temperature
    )
