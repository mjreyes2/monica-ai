"""
PDF Knowledge Base System for Monica AI
Indexes and searches scientific PDFs (especially human body/medical books)

Author: Marvin's AI Assistant
Date: 2025-12-12
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import pickle
from collections import defaultdict
import threading
import time

# Disable TensorFlow in transformers library (sentence-transformers only needs PyTorch)
os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['USE_TF'] = '0'

# Try to import PDF libraries
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("[PDF KB] pdfplumber not available. Install with: pip install pdfplumber")

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("[PDF KB] PyPDF2 not available. Install with: pip install PyPDF2")

# Try to import sentence transformers for semantic search (optional)
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_SEARCH_AVAILABLE = True
except (ImportError, RuntimeError, Exception) as e:
    SEMANTIC_SEARCH_AVAILABLE = False
    print(f"[PDF KB] Semantic search unavailable: {type(e).__name__}")
    print("[PDF KB] Keyword search will still work. To enable semantic search, fix dependencies.")


@dataclass
class PDFDocument:
    """Represents an indexed PDF document."""
    file_path: str
    title: str
    page_count: int
    indexed_date: float
    file_size: int
    file_hash: str  # For detecting changes
    metadata: Dict  # Author, subject, creation date, etc.


@dataclass
class PDFPage:
    """Represents a page from a PDF."""
    doc_path: str
    page_number: int
    text: str
    word_count: int


@dataclass
class SearchResult:
    """Result from knowledge base search."""
    doc_path: str
    doc_title: str
    page_number: int
    snippet: str  # Relevant text excerpt
    score: float  # Relevance score (0-1)
    context: str  # Surrounding context


class PDFKnowledgeBase:
    """
    PDF Knowledge Base for scientific documents.

    Features:
    - Indexes PDFs from specified directories
    - Full-text search
    - Semantic search (if sentence-transformers installed)
    - Caching for fast queries
    - Incremental indexing (only new/changed files)
    """

    def __init__(self, index_dir: Path = None):
        """
        Initialize PDF knowledge base.

        Args:
            index_dir: Directory to store index files (default: knowledge_base/)
        """
        self.index_dir = index_dir or Path("knowledge_base")
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Index files
        self.docs_index_file = self.index_dir / "documents.json"
        self.pages_index_file = self.index_dir / "pages.pkl"
        self.word_index_file = self.index_dir / "word_index.pkl"
        self.embeddings_file = self.index_dir / "embeddings.pkl"

        # In-memory indexes
        self.documents: Dict[str, PDFDocument] = {}  # {file_path: PDFDocument}
        self.pages: List[PDFPage] = []
        self.word_index: Dict[str, List[int]] = defaultdict(list)  # {word: [page_indices]}
        self.embeddings: Optional[np.ndarray] = None
        self.embedding_model: Optional[SentenceTransformer] = None

        # State
        self.is_indexed = False
        self.indexing_in_progress = False

        # Load existing index if available
        self._load_index()

        # Initialize semantic search if available
        if SEMANTIC_SEARCH_AVAILABLE:
            try:
                print("[PDF KB] Loading semantic search model...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("[PDF KB] Semantic search ready")
            except Exception as e:
                print(f"[PDF KB] Semantic search initialization failed: {e}")
                self.embedding_model = None

        print(f"[PDF KB] Knowledge base initialized ({len(self.documents)} documents indexed)")

    def _load_index(self):
        """Load existing index from disk."""
        try:
            # Load documents
            if self.docs_index_file.exists():
                with open(self.docs_index_file, 'r', encoding='utf-8') as f:
                    docs_data = json.load(f)
                    self.documents = {
                        path: PDFDocument(**data) for path, data in docs_data.items()
                    }
                print(f"[PDF KB] Loaded {len(self.documents)} documents from index")

            # Load pages
            if self.pages_index_file.exists():
                with open(self.pages_index_file, 'rb') as f:
                    self.pages = pickle.load(f)
                print(f"[PDF KB] Loaded {len(self.pages)} pages from index")

            # Load word index
            if self.word_index_file.exists():
                with open(self.word_index_file, 'rb') as f:
                    self.word_index = pickle.load(f)
                print(f"[PDF KB] Loaded word index ({len(self.word_index)} unique words)")

            # Load embeddings
            if self.embeddings_file.exists():
                with open(self.embeddings_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
                print(f"[PDF KB] Loaded embeddings ({self.embeddings.shape if self.embeddings is not None else 'None'})")

            self.is_indexed = len(self.documents) > 0

        except Exception as e:
            print(f"[PDF KB] Error loading index: {e}")

    def _save_index(self):
        """Save index to disk."""
        try:
            # Save documents
            docs_data = {path: asdict(doc) for path, doc in self.documents.items()}
            with open(self.docs_index_file, 'w', encoding='utf-8') as f:
                json.dump(docs_data, f, indent=2)

            # Save pages
            with open(self.pages_index_file, 'wb') as f:
                pickle.dump(self.pages, f)

            # Save word index
            with open(self.word_index_file, 'wb') as f:
                pickle.dump(dict(self.word_index), f)

            # Save embeddings
            if self.embeddings is not None:
                with open(self.embeddings_file, 'wb') as f:
                    pickle.dump(self.embeddings, f)

            print("[PDF KB] Index saved to disk")

        except Exception as e:
            print(f"[PDF KB] Error saving index: {e}")

    def index_directory(self, directory: Path, recursive: bool = True, extensions: List[str] = None) -> int:
        """
        Index all PDFs in a directory.

        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            extensions: File extensions to index (default: ['.pdf'])

        Returns:
            Number of new documents indexed
        """
        if extensions is None:
            extensions = ['.pdf']

        if self.indexing_in_progress:
            print("[PDF KB] Indexing already in progress")
            return 0

        self.indexing_in_progress = True
        print(f"[PDF KB] Indexing directory: {directory}")

        try:
            # Find all PDF files
            pdf_files = []
            if recursive:
                for ext in extensions:
                    pdf_files.extend(directory.rglob(f'*{ext}'))
            else:
                for ext in extensions:
                    pdf_files.extend(directory.glob(f'*{ext}'))

            print(f"[PDF KB] Found {len(pdf_files)} PDF files")

            new_count = 0
            for pdf_file in pdf_files:
                if self._index_pdf(pdf_file):
                    new_count += 1

            # Save index
            self._save_index()

            # Build embeddings if semantic search available
            if self.embedding_model and new_count > 0:
                self._build_embeddings()

            self.is_indexed = True
            print(f"[PDF KB] Indexing complete ({new_count} new documents)")

            return new_count

        except Exception as e:
            print(f"[PDF KB] Indexing error: {e}")
            return 0

        finally:
            self.indexing_in_progress = False

    def _index_pdf(self, pdf_path: Path) -> bool:
        """
        Index a single PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if newly indexed, False if skipped
        """
        try:
            # Check if already indexed and unchanged
            file_stat = pdf_path.stat()
            file_hash = f"{file_stat.st_size}_{file_stat.st_mtime}"

            if str(pdf_path) in self.documents:
                existing_doc = self.documents[str(pdf_path)]
                if existing_doc.file_hash == file_hash:
                    return False  # Already indexed, no changes

            print(f"[PDF KB] Indexing: {pdf_path.name}")

            # Extract PDF content
            pages_data = self._extract_pdf_text(pdf_path)
            if not pages_data:
                print(f"[PDF KB] Skipped (no text): {pdf_path.name}")
                return False

            # Get metadata
            metadata = self._extract_pdf_metadata(pdf_path)

            # Create document entry
            doc = PDFDocument(
                file_path=str(pdf_path),
                title=metadata.get('title', pdf_path.stem),
                page_count=len(pages_data),
                indexed_date=time.time(),
                file_size=file_stat.st_size,
                file_hash=file_hash,
                metadata=metadata
            )

            self.documents[str(pdf_path)] = doc

            # Add pages to index
            start_page_idx = len(self.pages)
            for page_num, page_text in enumerate(pages_data, start=1):
                page = PDFPage(
                    doc_path=str(pdf_path),
                    page_number=page_num,
                    text=page_text,
                    word_count=len(page_text.split())
                )
                self.pages.append(page)

                # Index words from this page
                page_idx = len(self.pages) - 1
                words = self._tokenize(page_text)
                for word in words:
                    self.word_index[word].append(page_idx)

            print(f"[PDF KB] Indexed: {pdf_path.name} ({len(pages_data)} pages)")
            return True

        except Exception as e:
            print(f"[PDF KB] Error indexing {pdf_path.name}: {e}")
            return False

    def _extract_pdf_text(self, pdf_path: Path) -> List[str]:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF

        Returns:
            List of page texts
        """
        pages = []

        # Try pdfplumber first (better text extraction)
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            pages.append(text.strip())
                return pages
            except Exception as e:
                print(f"[PDF KB] pdfplumber extraction failed: {e}, trying PyPDF2...")

        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                reader = PdfReader(str(pdf_path))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text.strip())
                return pages
            except Exception as e:
                print(f"[PDF KB] PyPDF2 extraction failed: {e}")

        return pages

    def _extract_pdf_metadata(self, pdf_path: Path) -> Dict:
        """Extract metadata from PDF."""
        metadata = {}

        if PYPDF2_AVAILABLE:
            try:
                reader = PdfReader(str(pdf_path))
                if reader.metadata:
                    metadata = {
                        'title': reader.metadata.get('/Title', pdf_path.stem),
                        'author': reader.metadata.get('/Author', 'Unknown'),
                        'subject': reader.metadata.get('/Subject', ''),
                        'creator': reader.metadata.get('/Creator', ''),
                        'producer': reader.metadata.get('/Producer', ''),
                        'creation_date': str(reader.metadata.get('/CreationDate', '')),
                    }
            except Exception as e:
                print(f"[PDF KB] Metadata extraction failed: {e}")

        # Ensure title exists
        if 'title' not in metadata or not metadata['title']:
            metadata['title'] = pdf_path.stem

        return metadata

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        # Lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        # Remove short words and common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in words if len(w) > 2 and w not in stopwords]
        return words

    def _build_embeddings(self):
        """Build semantic embeddings for all pages."""
        if not self.embedding_model or not self.pages:
            return

        print("[PDF KB] Building semantic embeddings...")
        try:
            texts = [page.text[:512] for page in self.pages]  # Limit to 512 chars
            self.embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            print(f"[PDF KB] Embeddings built ({self.embeddings.shape})")
            self._save_index()
        except Exception as e:
            print(f"[PDF KB] Embedding generation failed: {e}")

    def search(self, query: str, max_results: int = 10, use_semantic: bool = True) -> List[SearchResult]:
        """
        Search the knowledge base.

        Args:
            query: Search query
            max_results: Maximum results to return
            use_semantic: Use semantic search if available

        Returns:
            List of SearchResult objects, sorted by relevance
        """
        results = []

        # Try semantic search first (if available and requested)
        if use_semantic and self.embedding_model and self.embeddings is not None:
            results = self._semantic_search(query, max_results)

        # Fallback to keyword search
        if not results:
            results = self._keyword_search(query, max_results)

        return results

    def _keyword_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Keyword-based search."""
        query_words = self._tokenize(query)
        if not query_words:
            return []

        # Find pages containing query words
        page_scores = defaultdict(float)
        for word in query_words:
            if word in self.word_index:
                for page_idx in self.word_index[word]:
                    page_scores[page_idx] += 1.0

        # Sort by score
        sorted_pages = sorted(page_scores.items(), key=lambda x: x[1], reverse=True)
        sorted_pages = sorted_pages[:max_results]

        # Build results
        results = []
        for page_idx, score in sorted_pages:
            page = self.pages[page_idx]
            doc = self.documents.get(page.doc_path)

            # Find snippet containing query words
            snippet = self._extract_snippet(page.text, query_words)

            result = SearchResult(
                doc_path=page.doc_path,
                doc_title=doc.title if doc else Path(page.doc_path).stem,
                page_number=page.page_number,
                snippet=snippet,
                score=score / len(query_words),  # Normalize score
                context=page.text[:500]  # First 500 chars as context
            )
            results.append(result)

        return results

    def _semantic_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Semantic search using embeddings."""
        if not self.embedding_model or self.embeddings is None:
            return []

        try:
            # Encode query
            query_embedding = self.embedding_model.encode([query])[0]

            # Calculate cosine similarity
            similarities = np.dot(self.embeddings, query_embedding) / (
                np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
            )

            # Get top results
            top_indices = np.argsort(similarities)[::-1][:max_results]

            # Build results
            results = []
            for idx in top_indices:
                page = self.pages[idx]
                doc = self.documents.get(page.doc_path)
                score = float(similarities[idx])

                result = SearchResult(
                    doc_path=page.doc_path,
                    doc_title=doc.title if doc else Path(page.doc_path).stem,
                    page_number=page.page_number,
                    snippet=page.text[:300],  # First 300 chars
                    score=score,
                    context=page.text[:500]
                )
                results.append(result)

            return results

        except Exception as e:
            print(f"[PDF KB] Semantic search error: {e}")
            return []

    def _extract_snippet(self, text: str, query_words: List[str], context_words: int = 30) -> str:
        """Extract relevant snippet from text."""
        text_lower = text.lower()

        # Find first occurrence of any query word
        best_pos = -1
        for word in query_words:
            pos = text_lower.find(word)
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos

        if best_pos == -1:
            return text[:200]  # No match, return beginning

        # Extract context around match
        words = text.split()
        word_positions = []
        current_pos = 0
        for i, word in enumerate(words):
            if current_pos >= best_pos:
                start_idx = max(0, i - context_words // 2)
                end_idx = min(len(words), i + context_words // 2)
                snippet = ' '.join(words[start_idx:end_idx])
                if start_idx > 0:
                    snippet = '...' + snippet
                if end_idx < len(words):
                    snippet = snippet + '...'
                return snippet
            current_pos += len(word) + 1

        return text[:200]

    def get_statistics(self) -> Dict:
        """Get knowledge base statistics."""
        total_words = sum(page.word_count for page in self.pages)
        total_size = sum(doc.file_size for doc in self.documents.values())

        return {
            'total_documents': len(self.documents),
            'total_pages': len(self.pages),
            'total_words': total_words,
            'unique_words': len(self.word_index),
            'total_size_mb': total_size / (1024 * 1024),
            'semantic_search_available': self.embeddings is not None,
            'indexed': self.is_indexed,
        }


# Example usage
if __name__ == "__main__":
    print("PDF Knowledge Base - Test Mode")
    print("=" * 60)

    kb = PDFKnowledgeBase()

    print("\nTo index PDFs from D: drive:")
    print("  kb.index_directory(Path('D:/'), recursive=True)")

    print("\nTo search:")
    print("  results = kb.search('heart anatomy')")

    print("\nStatistics:")
    stats = kb.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
