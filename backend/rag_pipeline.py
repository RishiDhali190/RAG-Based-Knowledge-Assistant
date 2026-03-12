"""
RAG Pipeline Module
===================
The core of the system: FAISS vector store + retrieval + LLM response generation.

Flow:
  1. Documents are chunked and embedded → stored in FAISS
  2. User asks a question → question is embedded
  3. FAISS finds the top-K most similar chunks (similarity search)
  4. Those chunks are sent as context to the LLM
  5. LLM generates an answer grounded in the retrieved context

Two modes:
  - rag_query()    → answers using retrieved document chunks (accurate)
  - direct_query() → answers without any context (may hallucinate)

LLM: Groq API (FREE — 30 req/min, no credit card needed)
Uses Llama 3 8B model — fast and capable
"""

import os
import json
import numpy as np
import faiss
from groq import Groq
from embeddings import get_embeddings, get_embedding_dimension


# ══════════════════════════════════════════════════════════════════════
#  FAISS VECTOR STORE
# ══════════════════════════════════════════════════════════════════════

class FAISSStore:
    """A wrapper around FAISS for storing and searching document chunk embeddings."""
    
    def __init__(self, store_dir: str = "../vector_store"):
        self.store_dir = store_dir
        self.index = None
        self.chunks: list[str] = []
        self.metadata: list[dict] = []
        self.dimension = get_embedding_dimension()
        os.makedirs(store_dir, exist_ok=True)
        self._load()
    
    def add_documents(self, chunks: list[str], source_filename: str):
        if not chunks:
            return
        embeddings = get_embeddings(chunks)
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)
        for i, chunk in enumerate(chunks):
            self.chunks.append(chunk)
            self.metadata.append({"source": source_filename, "chunk_index": i})
        self._save()
        print(f"✅ Added {len(chunks)} chunks from '{source_filename}' to FAISS index")
        print(f"   Total chunks in index: {len(self.chunks)}")
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self.index is None or self.index.ntotal == 0:
            return []
        query_embedding = get_embeddings([query])
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            results.append({
                "text": self.chunks[idx],
                "source": self.metadata[idx]["source"],
                "score": float(dist)
            })
        return results
    
    def get_document_list(self) -> list[str]:
        return list(set(m["source"] for m in self.metadata))
    
    def get_total_chunks(self) -> int:
        return len(self.chunks)
    
    def clear(self):
        self.index = None
        self.chunks = []
        self.metadata = []
        self._save()
    
    def _save(self):
        if self.index is not None:
            faiss.write_index(self.index, os.path.join(self.store_dir, "index.faiss"))
        data = {"chunks": self.chunks, "metadata": self.metadata}
        with open(os.path.join(self.store_dir, "store_data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load(self):
        index_path = os.path.join(self.store_dir, "index.faiss")
        data_path = os.path.join(self.store_dir, "store_data.json")
        if os.path.exists(index_path) and os.path.exists(data_path):
            self.index = faiss.read_index(index_path)
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks = data["chunks"]
            self.metadata = data["metadata"]
            print(f"📂 Loaded existing FAISS index with {len(self.chunks)} chunks")


# ══════════════════════════════════════════════════════════════════════
#  GROQ LLM (FREE — 30 requests/min, no credit card needed)
#  Uses Llama 3 8B — fast inference on Groq's hardware
# ══════════════════════════════════════════════════════════════════════

_groq_client = None

MODEL = "llama-3.1-8b-instant"


def _get_groq_client():
    """Initialize the Groq client (singleton)."""
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError(
                "Groq API key not configured. "
                "Set GROQ_API_KEY environment variable. "
                "Get a FREE key at: https://console.groq.com/keys"
            )
        _groq_client = Groq(api_key=api_key)
        print(f"✅ Groq client initialized (model: {MODEL})!")
    return _groq_client


# ══════════════════════════════════════════════════════════════════════
#  LLM QUERY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def rag_query(question: str, store: FAISSStore, top_k: int = 5) -> dict:
    """Answer a question using RAG (retrieval + LLM)."""
    results = store.search(question, top_k=top_k)
    
    if not results:
        return {
            "answer": "No documents have been uploaded yet. Please upload documents first.",
            "sources": [],
            "mode": "rag"
        }
    
    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(f"[Source: {r['source']}]\n{r['text']}")
    context = "\n\n---\n\n".join(context_parts)
    
    system_prompt = """You are a helpful knowledge assistant. Answer the user's question 
based ONLY on the provided context from company documents.

Rules:
- Only use information from the provided context
- If the context doesn't contain enough information to answer, say so clearly
- Reference which document(s) the information comes from
- Be concise and accurate
- Do not make up or assume information not in the context"""

    user_prompt = f"""Context from company documents:

{context}

---

Question: {question}

Please answer based only on the context above."""
    
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        answer = response.choices[0].message.content
    except ValueError as e:
        answer = f"⚠️ {str(e)}\n\nHowever, here are the relevant document chunks I found:\n\n{context}"
    except Exception as e:
        answer = f"Error calling LLM: {str(e)}\n\nRelevant chunks found:\n\n{context}"
    
    return {
        "answer": answer,
        "sources": results,
        "mode": "rag"
    }


def direct_query(question: str) -> dict:
    """Answer a question WITHOUT RAG (for hallucination demo)."""
    system_prompt = """You are a helpful assistant. Answer the user's question 
to the best of your knowledge. If you're not sure about something, 
provide your best answer anyway."""

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        answer = response.choices[0].message.content
    except ValueError as e:
        answer = f"⚠️ {str(e)}"
    except Exception as e:
        answer = f"Error calling LLM: {str(e)}"
    
    return {
        "answer": answer,
        "sources": [],
        "mode": "no-rag"
    }
