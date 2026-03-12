"""
Document Loader Module
======================
Handles loading and chunking of PDF, DOCX, and TXT documents.

How it works:
1. load_document() reads the raw text from a file based on its type
2. chunk_text() splits that text into smaller overlapping pieces
   so the vector search can find precise answers
"""

import os
from PyPDF2 import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_pdf(file_path: str) -> str:
    """Extract all text from a PDF file, page by page."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def load_docx(file_path: str) -> str:
    """Extract all text from a Word (.docx) file, paragraph by paragraph."""
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text + "\n"
    return text


def load_txt(file_path: str) -> str:
    """Read a plain text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_document(file_path: str) -> str:
    """
    Load a document and return its text content.
    
    Supports:
      - .pdf  → uses PyPDF2
      - .docx → uses python-docx
      - .txt  → plain file read
    
    Args:
        file_path: Path to the document file
    
    Returns:
        The full text content of the document
    
    Raises:
        ValueError: If the file type is not supported
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext == ".docx":
        return load_docx(file_path)
    elif ext == ".txt":
        return load_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .docx, .txt")


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    Split text into smaller, overlapping chunks for better retrieval.
    
    Why chunking?
    - Large documents can't be searched efficiently as a whole
    - Smaller chunks let us find the most relevant piece of information
    - Overlap ensures we don't cut sentences in the middle
    
    Args:
        text: The full document text
        chunk_size: Maximum characters per chunk (default 500)
        chunk_overlap: Number of overlapping characters between chunks (default 50)
    
    Returns:
        List of text chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_text(text)
    return chunks
