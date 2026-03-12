"""
FastAPI Backend – Main Entry Point
===================================
Provides REST API endpoints for the RAG Knowledge Assistant.

Endpoints:
  POST /upload       → Upload documents (PDF, DOCX, TXT)
  POST /query        → Ask a question (RAG mode with document context)
  POST /query-no-rag → Ask a question (direct LLM, for hallucination demo)
  GET  /documents    → List uploaded documents
  DELETE /clear      → Clear all documents and reset the index

Run with:
  cd backend
  uvicorn main:app --reload --port 8000
"""

import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from document_loader import load_document, chunk_text
from rag_pipeline import FAISSStore, rag_query, direct_query

# ── App Setup ──────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Knowledge Assistant",
    description="Chat with your company documents using RAG",
    version="1.0.0"
)

# Allow React frontend (running on port 5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to temporarily store uploaded files
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize the FAISS vector store
vector_store = FAISSStore(store_dir=os.path.join(os.path.dirname(__file__), "..", "vector_store"))


# ── Request/Response Models ────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    mode: str


# ── Endpoints ──────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    """
    Upload one or more documents for RAG processing.
    
    What happens when you upload:
    1. File is saved temporarily to disk
    2. Text is extracted (PDF/DOCX/TXT)
    3. Text is split into chunks (500 chars each, 50 overlap)
    4. Chunks are converted to embeddings
    5. Embeddings are stored in FAISS vector database
    6. Temporary file is cleaned up
    """
    results = []
    
    for file in files:
        # Validate file type
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".pdf", ".docx", ".txt"]:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT."
            })
            continue
        
        try:
            # Step 1: Save file temporarily
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Step 2: Extract text
            text = load_document(file_path)
            
            if not text.strip():
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "No text could be extracted from this file."
                })
                continue
            
            # Step 3: Chunk the text
            chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
            
            # Step 4 & 5: Embed and store in FAISS
            vector_store.add_documents(chunks, source_filename=file.filename)
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "chunks_created": len(chunks),
                "message": f"Successfully processed: {len(chunks)} chunks created"
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
        
        finally:
            # Step 6: Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    return {
        "results": results,
        "total_chunks_in_store": vector_store.get_total_chunks()
    }


@app.post("/query", response_model=QueryResponse)
async def query_with_rag(request: QueryRequest):
    """
    Ask a question → system retrieves relevant chunks → LLM answers using them.
    
    This is the RAG mode:
    - AI reads the relevant parts of your documents FIRST
    - Then generates an answer based ONLY on what it found
    - This prevents hallucination
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    result = rag_query(request.question, vector_store, top_k=request.top_k)
    return QueryResponse(**result)


@app.post("/query-no-rag", response_model=QueryResponse)
async def query_without_rag(request: QueryRequest):
    """
    Ask a question → LLM answers WITHOUT any document context.
    
    This is for the hallucination comparison demo:
    - AI answers purely from its training data
    - It may guess or make up information
    - Compare this with RAG answers to see the difference
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    result = direct_query(request.question)
    return QueryResponse(**result)


@app.get("/documents")
async def list_documents():
    """List all documents that have been uploaded and indexed."""
    return {
        "documents": vector_store.get_document_list(),
        "total_chunks": vector_store.get_total_chunks()
    }


@app.delete("/clear")
async def clear_store():
    """Clear all documents and reset the vector store."""
    vector_store.clear()
    # Also clear uploads directory
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    return {"message": "All documents cleared successfully"}


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "app": "RAG Knowledge Assistant",
        "documents_loaded": len(vector_store.get_document_list()),
        "total_chunks": vector_store.get_total_chunks()
    }
