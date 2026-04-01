"""
Embedding Module
Supports: Gemini Embedding API (cloud) or Vietnamese local model (fallback)
"""
import os

try:
    from langchain_core.embeddings import Embeddings
except ImportError:
    from langchain.embeddings.base import Embeddings

from core.config import GEMINI_API_KEY


class GeminiEmbedding(Embeddings):
    """
    Google Gemini Embedding via REST API (v1 endpoint).
    Uses text-embedding-004 model — lightweight, no local GPU/RAM needed.
    """
    
    def __init__(self, model: str = "text-embedding-004"):
        import requests as _req
        self._requests = _req
        self.model = model
        self.api_key = GEMINI_API_KEY
        self.base_url = f"https://generativelanguage.googleapis.com/v1/models/{model}"
        
        # Verify model is accessible
        print(f"Loading Gemini Embedding API: {model}")
        test = self._embed_batch(["test"])
        if test:
            print(f"✓ Gemini Embedding ready ({len(test[0])} dimensions, cloud API)")
        else:
            raise RuntimeError("Failed to connect to Gemini Embedding API")
    
    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Call Gemini REST API to embed a batch of texts."""
        requests_body = [
            {"model": f"models/{self.model}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        
        resp = self._requests.post(
            f"{self.base_url}:batchEmbedContents",
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json={"requests": requests_body},
        )
        
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini Embedding API error {resp.status_code}: {resp.text}")
        
        data = resp.json()
        return [e["values"] for e in data["embeddings"]]
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        all_embeddings = []
        batch_size = 100  # Gemini supports up to 100 per batch
        
        print(f"    - Embedding {len(texts)} chunks via Gemini API...")
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            
            done = min(i + batch_size, len(texts))
            print(f"      ✓ Processed {done}/{len(texts)} chunks")
        
        return all_embeddings
    
    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]
    
    def get_embedding_function(self):
        return self


class VietnameseEmbedding(Embeddings):
    """
    Local Vietnamese embedding model (fallback for offline use).
    Requires sentence-transformers + ~400MB RAM.
    """
    
    def __init__(self, model_name: str = "dangvantuan/vietnamese-embedding"):
        from langchain_huggingface import HuggingFaceEmbeddings
        print(f"Loading Vietnamese embedding model: {model_name}")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 16,
            }
        )
        
        if hasattr(self.embeddings, 'client'):
            self.embeddings.client.max_seq_length = 256
            if hasattr(self.embeddings.client, 'tokenizer'):
                self.tokenizer = self.embeddings.client.tokenizer
                self.tokenizer.model_max_length = 256
            else:
                from transformers import AutoTokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        else:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        print(f"✓ Model loaded successfully (768 dimensions, max_seq_length=256)")
    
    def _truncate_by_tokens(self, text: str, max_tokens: int = 200) -> str:
        try:
            tokens = self.tokenizer.encode(text, add_special_tokens=False)
            if len(tokens) > max_tokens:
                truncated_tokens = tokens[:max_tokens]
                return self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
            return text
        except Exception:
            return text[:300]
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        safe_texts = [self._truncate_by_tokens(t) for t in texts]
        all_embeddings = []
        batch_size = 16
        
        print(f"    - Embedding {len(safe_texts)} chunks in batches of {batch_size}...")
        for i in range(0, len(safe_texts), batch_size):
            batch = safe_texts[i : i + batch_size]
            batch_embeddings = self.embeddings.embed_documents(batch)
            all_embeddings.extend(batch_embeddings)
            
            if (i + batch_size) % 64 == 0 or (i + batch_size) >= len(safe_texts):
                print(f"      ✓ Processed {min(i + batch_size, len(safe_texts))}/{len(safe_texts)} chunks")
        
        return all_embeddings
    
    def embed_query(self, text: str) -> list[float]:
        safe_text = self._truncate_by_tokens(text)
        return self.embeddings.embed_query(safe_text)
    
    def get_embedding_function(self):
        return self


# ══════════════════════════════════════════════════════════════
# Singleton
# ══════════════════════════════════════════════════════════════
_embedding_instance = None


def get_vietnamese_embeddings():
    """
    Get or create singleton embedding instance.
    Uses Gemini API if GEMINI_API_KEY is set, otherwise falls back to local model.
    """
    global _embedding_instance
    if _embedding_instance is None:
        if GEMINI_API_KEY:
            _embedding_instance = GeminiEmbedding()
        else:
            print("⚠ No GEMINI_API_KEY — falling back to local Vietnamese embedding model")
            _embedding_instance = VietnameseEmbedding()
    return _embedding_instance
