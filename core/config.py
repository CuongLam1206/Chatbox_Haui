"""
Configuration settings for Agentic RAG Chatbot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory (trỏ về thư mục gốc dự án, không phải core/)
BASE_DIR = Path(__file__).parent.parent

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model Configuration
EMBEDDING_MODEL = "dangvantuan/vietnamese-embedding"  # Best Vietnamese embedding model

# LLM Configuration (with Ollama fallback)
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() == "true"
USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-72b-instruct:free")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")  # Good Vietnamese support

if USE_GEMINI:
    LLM_MODEL = GEMINI_MODEL
elif USE_OPENROUTER:
    LLM_MODEL = OPENROUTER_MODEL
elif USE_GROQ:
    LLM_MODEL = GROQ_MODEL
elif USE_OLLAMA:
    LLM_MODEL = OLLAMA_MODEL
else:
    LLM_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.3  # Lower temperature for more consistent, faster responses

# Paths
DOCUMENT_DIR = BASE_DIR / "data" / "documents"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
TRACKER_FILE = BASE_DIR / "data" / "last_update.json"

# Ensure directories exist
DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGODB_DATABASE", "chatbot_db")
MONGO_COLLECTION = "conversations"

# RAG Parameters
CHUNK_SIZE = 2000  # Increased to keep appendices/forms intact in single chunk
CHUNK_OVERLAP = 200
RETRIEVAL_K = 12  # Increased from 8 to improve recall for location queries
RELEVANCE_THRESHOLD = 0.2

# Agent Configuration
MAX_RETRIES = 1  # Reduced retries for faster response
ENABLE_HALLUCINATION_CHECK = False  # Disabled to save time and tokens
