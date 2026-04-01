"""
Vietnamese Embedding Module
Using dangvantuan/vietnamese-embedding (PhoBERT-based, 84.87% STS score)
"""
from langchain_huggingface import HuggingFaceEmbeddings
try:
    from langchain_core.embeddings import Embeddings
except ImportError:
    from langchain.embeddings.base import Embeddings
from core.config import EMBEDDING_MODEL


class VietnameseEmbedding(Embeddings):
    """
    Wrapper for Vietnamese embedding model
    Inherits from LangChain Embeddings to ensure consistent behavior.
    Uses PhoBERT-based sentence transformer optimized for Vietnamese.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize Vietnamese embedding model
        
        Args:
            model_name: HuggingFace model identifier
        """
        print(f"Loading Vietnamese embedding model: {model_name}")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 16,
            }
        )
        
        # Manually set max_seq_length and force truncation behavior
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
        """
        Truncate text by tokens to be 100% sure it fits in model window
        Uses 200 as a safe limit (model usually supports 512, but PhoBERT often 256)
        """
        try:
            tokens = self.tokenizer.encode(text, add_special_tokens=False)
            if len(tokens) > max_tokens:
                # print(f"    ⚠️ Truncating chunk from {len(tokens)} to {max_tokens} tokens")
                truncated_tokens = tokens[:max_tokens]
                return self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
            return text
        except Exception:
            # Fallback to character truncation if tokenizer fails
            return text[:300]
    
    def _truncate_text(self, text: str, max_chars: int = 300) -> str:
        """
        Truncate text to safe size for embedding
        300 chars ≈ 180 tokens for Vietnamese (very safe for PhoBERT 256 limit)
        """
        if len(text) > max_chars:
            # print(f"    ⚠️ Truncating chunk from {len(text)} to {max_chars} chars")
            return text[:max_chars]
        return text
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of documents with safety truncation, manual batching and error logging
        """
        if not texts:
            return []
            
        # Truncate all texts using token-level precision
        safe_texts = [self._truncate_by_tokens(t) for t in texts]
        
        all_embeddings = []
        batch_size = 16  # Very small batch for stability
        
        try:
            print(f"    - Embedding {len(safe_texts)} chunks in batches of {batch_size}...")
            for i in range(0, len(safe_texts), batch_size):
                batch = safe_texts[i : i + batch_size]
                try:
                    batch_embeddings = self.embeddings.embed_documents(batch)
                    all_embeddings.extend(batch_embeddings)
                except Exception as batch_error:
                    print(f"\n❌ BATCH ERROR at index {i}: {str(batch_error)}")
                    # Test each chunk in the failing batch individually
                    for j, failing_text in enumerate(batch):
                        try:
                            self.embeddings.embed_query(failing_text)
                        except Exception as individual_error:
                            print(f"\nCRITICAL: Found failing chunk at global index {i + j}")
                            print(f"Length: {len(failing_text)}")
                            print(f"Text snippet: {failing_text[:100]}...")
                            print(f"Error: {str(individual_error)}")
                            # We still raise to stop the process
                            raise individual_error
                    raise batch_error
                
                if (i + batch_size) % 64 == 0 or (i + batch_size) >= len(safe_texts):
                    print(f"      ✓ Processed {min(i + batch_size, len(safe_texts))}/{len(safe_texts)} chunks")
            
            return all_embeddings
            
        except Exception as e:
            print(f"❌ EMBEDDING ERROR DETECTED: {str(e)}")
            # Log first few chunks of the failing batch
            # Note: We can find the exact failing batch by checking current 'i'
            raise e
    
    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query with safety truncation
        """
        safe_text = self._truncate_by_tokens(text)
        return self.embeddings.embed_query(safe_text)
    
    def get_embedding_function(self):
        """
        Get this instance as the embedding function for use with vector stores.
        Returns the wrapper itself to ensure truncation is applied.
        """
        return self


# Singleton instance
_embedding_instance = None


def get_vietnamese_embeddings() -> VietnameseEmbedding:
    """
    Get or create singleton Vietnamese embedding instance
    
    Returns:
        VietnameseEmbedding instance
    """
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = VietnameseEmbedding()
    return _embedding_instance
