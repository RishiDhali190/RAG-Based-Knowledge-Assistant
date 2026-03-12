# 🧠 RAG-Based Knowledge Assistant

**Chat with your company documents using AI-powered Retrieval Augmented Generation.**

Upload PDF, DOCX, or TXT files and ask questions — the system searches your documents first, then generates accurate, grounded answers using an LLM.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Document Upload** | Upload PDF, DOCX, TXT with drag & drop |
| ✂️ **Smart Chunking** | Splits documents into searchable 500-char chunks |
| 🔢 **Embeddings** | Converts text to vectors using Sentence Transformers (local, free) |
| 🗄️ **FAISS Vector DB** | Stores embeddings for fast similarity search |
| 🔍 **Retrieval** | Finds top-K relevant chunks for each question |
| 🤖 **LLM Grounding** | GPT-3.5-turbo answers based ONLY on retrieved context |
| 💬 **Chat Interface** | Modern React UI with message history |
| 🔀 **Hallucination Demo** | Side-by-side comparison: RAG vs non-RAG answers |

---

## 🛠️ Tech Stack

- **Frontend:** React + Vite
- **Backend:** Python FastAPI
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`)
- **Vector DB:** FAISS
- **LLM:** OpenAI GPT-3.5-turbo
- **Document Processing:** LangChain + PyPDF2 + python-docx

---

## 📁 Project Structure

```
RAG Based Knowledge Assistance/
├── backend/
│   ├── main.py              # FastAPI server (endpoints)
│   ├── document_loader.py   # PDF/DOCX/TXT loading + chunking
│   ├── embeddings.py        # Sentence Transformer embeddings
│   ├── rag_pipeline.py      # FAISS store + RAG query logic
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Root component
│   │   ├── main.jsx          # Entry point
│   │   ├── index.css         # Design system (dark theme)
│   │   └── components/
│   │       ├── ChatPanel.jsx    # Chat messages + input
│   │       └── UploadPanel.jsx  # File upload sidebar
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── vector_store/             # FAISS index (auto-created)
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
set OPENAI_API_KEY=sk-your-key-here        # Windows
# export OPENAI_API_KEY=sk-your-key-here   # Mac/Linux

# Start the server
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.

### 2. Frontend Setup

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 3. Use the App

1. Open `http://localhost:5173` in your browser
2. **Upload documents** using the sidebar (drag & drop or click)
3. **Ask questions** in the chat input
4. **Toggle "Compare RAG vs No-RAG"** to see the hallucination demo

---

## 🧪 How RAG Works (Step by Step)

```
User uploads document
        ↓
Text extracted (PDF/DOCX/TXT)
        ↓
Text split into chunks (500 chars each)
        ↓
Chunks converted to embeddings (vectors)
        ↓
Vectors stored in FAISS index
        ↓
User asks a question
        ↓
Question converted to embedding
        ↓
FAISS finds most similar chunks
        ↓
Chunks + question sent to LLM
        ↓
LLM generates answer from context only
        ↓
Answer displayed with source references
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload documents (multipart form) |
| `POST` | `/query` | Ask with RAG (retrieval + LLM) |
| `POST` | `/query-no-rag` | Ask without RAG (hallucination demo) |
| `GET` | `/documents` | List uploaded documents |
| `DELETE` | `/clear` | Clear all documents and index |
| `GET` | `/` | Health check |

---

## 🔀 Hallucination Reduction Demo

Toggle **"Compare RAG vs No-RAG"** in the top bar to see:

| RAG Mode ✅ | No-RAG Mode ❌ |
|-------------|----------------|
| Searches documents first | Answers from memory only |
| Grounded in real data | May hallucinate facts |
| Shows source references | No sources available |
| Accurate for company docs | Guesses at company-specific info |

---

## 📝 License

MIT License — feel free to use this for learning and demonstration purposes.
