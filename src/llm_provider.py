"""
LLM Provider with automatic fallbacks
"""
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from core.config import (
    OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY,
    USE_OLLAMA, USE_GROQ, USE_OPENROUTER, USE_GEMINI,
    OLLAMA_BASE_URL, OLLAMA_MODEL, GROQ_MODEL, OPENROUTER_MODEL, GEMINI_MODEL,
    LLM_MODEL, TEMPERATURE
)

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
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=temperature,
            google_api_key=GEMINI_API_KEY,
            convert_system_message_to_human=True
        )

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
