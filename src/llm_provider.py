"""
LLM Provider with automatic fallbacks and retry logic for rate limits
"""
import time
import functools
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


class RetryLLMWrapper:
    """
    Wraps a LangChain LLM/ChatModel to add automatic retry with exponential
    backoff when rate-limited (HTTP 429).
    Transparently proxies all attributes so agents see no difference.
    """

    def __init__(self, llm, max_retries=MAX_RETRIES, base_delay=BASE_DELAY):
        self._llm = llm
        self._max_retries = max_retries
        self._base_delay = base_delay

    # -- Proxy attribute access to the inner LLM --
    def __getattr__(self, name):
        attr = getattr(self._llm, name)
        # Wrap callable methods that hit the API
        if callable(attr) and name in ("invoke", "ainvoke", "generate", "agenerate",
                                        "predict", "apredict", "batch", "abatch"):
            return self._wrap_with_retry(attr, name)
        return attr

    def _wrap_with_retry(self, method, method_name):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, self._max_retries + 1):
                try:
                    return method(*args, **kwargs)
                except Exception as exc:
                    if _is_rate_limit_error(exc):
                        delay = min(self._base_delay * (2 ** (attempt - 1)), MAX_DELAY)
                        print(f"[LLM Retry] Rate limited on {method_name} "
                              f"(attempt {attempt}/{self._max_retries}). "
                              f"Waiting {delay}s...")
                        time.sleep(delay)
                        last_exc = exc
                    else:
                        raise  # Non-rate-limit errors bubble up immediately
            print(f"[LLM Retry] All {self._max_retries} retries exhausted for {method_name}.")
            raise last_exc
        return wrapper

    # -- Support pipe operator (prompt | llm) used by LangChain --
    def __or__(self, other):
        return self._llm.__or__(other)

    def __ror__(self, other):
        return self._llm.__ror__(other)

    # -- Support with_structured_output for Router/Grader --
    def with_structured_output(self, schema, **kwargs):
        structured = self._llm.with_structured_output(schema, **kwargs)
        return RetryLLMWrapper(structured, self._max_retries, self._base_delay)
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
