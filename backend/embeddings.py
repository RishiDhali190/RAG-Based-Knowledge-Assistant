"""
Embeddings Module
=================
Converts text into numerical vectors (embeddings) using Sentence Transformers.

How it works:
- Text like "Company leave policy" becomes a list of numbers: [0.23, 0.44, ...]
- Similar texts produce similar numbers (vectors)
- This allows us to search by meaning, not just keywords

Example:
    "vacation rules" and "leave policy" will have similar embeddings
    even though they use different words.

Model used: all-MiniLM-L6-v2
- Fast, lightweight (80MB)
- Produces 384-dimensional vectors
- Runs locally, no API key needed
"""

import numpy as np
from sentence_transformers import SentenceTransformer

# ── Singleton Pattern ──────────────────────────────────────────────────
# Load the model once and reuse it for all requests.
# This avoids reloading the model (which takes several seconds) on every call.

_model = None


def _get_model() -> SentenceTransformer:
    """Get or initialize the sentence transformer model (singleton)."""
    global _model
    if _model is None:
        print("⏳ Loading embedding model (first time only)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Embedding model loaded successfully!")
    return _model


# ── Public API ─────────────────────────────────────────────────────────

def get_embeddings(texts: list[str]) -> np.ndarray:
    """
    Convert a list of text strings into vector embeddings.
    
    Args:
        texts: List of text chunks to embed
        
    Returns:
        numpy array of shape (len(texts), 384)
        Each row is the embedding vector for the corresponding text.
    
    Example:
        >>> embeddings = get_embeddings(["Hello world", "Leave policy"])
        >>> embeddings.shape
        (2, 384)
    """
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings.astype("float32")


def get_embedding_dimension() -> int:
    """Return the dimensionality of the embeddings (384 for MiniLM)."""
    model = _get_model()
    return model.get_sentence_embedding_dimension()
