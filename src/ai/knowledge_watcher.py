"""
Monica AI - Knowledge Base Auto-Update Watcher

Watches the Knowledge Base folders for new PDFs, research articles, and documents.
When a new file is added, Monica automatically:
1. Detects the file type (PDF, TXT, DOCX, MD, etc.)
2. Extracts text content
3. Chunks it for RAG retrieval
4. Updates the local search index
5. Notifies the AI service that new knowledge is available

Usage:
    from ai.knowledge_watcher import get_knowledge_watcher
    watcher = get_knowledge_watcher()
    watcher.start()  # Begins monitoring in background thread
    
Drop files into: data/Monica_Knowledge_Base/
Monica will auto-integrate them within seconds.
"""

import os
import sys
import time
import json
import hashlib
import logging
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("Monica.KnowledgeWatcher")


@dataclass
class DocumentChunk:
    """A chunk of text from a document."""
    text: str
    source_file: str
    page: int
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexedDocument:
    """Record of an indexed document."""
    file_path: str
    file_hash: str
    file_size: int
    num_chunks: int
    indexed_at: str
    file_type: str


class PDFTextExtractor:
    """Extracts text from PDF files using multiple backends."""

    def __init__(self):
        self._backend = None
        # Try backends in order of preference
        try:
            import fitz  # PyMuPDF - fastest and most accurate
            self._backend = 'pymupdf'
            logger.info("[KB_WATCH] PDF backend: PyMuPDF (fast, accurate)")
        except ImportError:
            pass

        if not self._backend:
            try:
                from pdfminer.high_level import extract_text
                self._backend = 'pdfminer'
                logger.info("[KB_WATCH] PDF backend: pdfminer")
            except ImportError:
                pass

        if not self._backend:
            try:
                import PyPDF2
                self._backend = 'pypdf2'
                logger.info("[KB_WATCH] PDF backend: PyPDF2")
            except ImportError:
                pass

        if not self._backend:
            logger.warning("[KB_WATCH] No PDF backend available. Install: pip install PyMuPDF")

    def extract(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract text from PDF, returning list of {page, text} dicts.
        """
        pages = []
        try:
            if self._backend == 'pymupdf':
                import fitz
                doc = fitz.open(str(file_path))
                for i, page in enumerate(doc):
                    text = page.get_text("text")
                    if text.strip():
                        pages.append({"page": i + 1, "text": text.strip()})
                    else:
                        # Scanned/image PDF — try OCR via pytesseract
                        ocr_text = self._ocr_page(page)
                        if ocr_text.strip():
                            pages.append({"page": i + 1, "text": ocr_text.strip()})
                doc.close()

            elif self._backend == 'pdfminer':
                from pdfminer.high_level import extract_text
                text = extract_text(str(file_path))
                if text.strip():
                    # pdfminer doesn't give per-page, treat as single page
                    pages.append({"page": 1, "text": text.strip()})

            elif self._backend == 'pypdf2':
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for i, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text and text.strip():
                            pages.append({"page": i + 1, "text": text.strip()})
            else:
                logger.warning(f"[KB_WATCH] No PDF backend to extract: {file_path.name}")

        except Exception as e:
            logger.error(f"[KB_WATCH] PDF extraction error ({file_path.name}): {e}")

        return pages

    def _ocr_page(self, page) -> str:
        """OCR a scanned PDF page using pytesseract or PyMuPDF built-in OCR."""
        # Configure Tesseract path on Windows
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        # Method 1: pytesseract + Tesseract binary
        try:
            import pytesseract
            from PIL import Image
            import io
            import os
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            import fitz
            mat = fitz.Matrix(300 / 72, 300 / 72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img, lang='eng')
            if text and text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"[KB_WATCH] pytesseract OCR failed: {e}")

        # Method 2: PyMuPDF built-in OCR (requires Tesseract in PATH)
        try:
            tp = page.get_textpage_ocr(language="eng", dpi=300, full=True)
            text = page.get_text("text", textpage=tp)
            if text and text.strip():
                return text
        except Exception as e:
            logger.debug(f"[KB_WATCH] PyMuPDF OCR failed: {e}")

        return ""


class TextExtractor:
    """Extracts text from various document formats."""

    def __init__(self):
        self.pdf_extractor = PDFTextExtractor()

    def extract(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract text from a file, returning list of {page, text} dicts.
        Supports: PDF, TXT, MD, JSON, CSV, DOCX
        """
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self.pdf_extractor.extract(file_path)

        elif suffix in ('.txt', '.md', '.rst', '.log'):
            try:
                text = file_path.read_text(encoding='utf-8', errors='replace')
                if text.strip():
                    return [{"page": 1, "text": text.strip()}]
            except Exception as e:
                logger.error(f"[KB_WATCH] Text read error ({file_path.name}): {e}")
            return []

        elif suffix == '.json':
            try:
                with open(str(file_path), 'r', encoding='utf-8', errors='replace') as fh:
                    raw = fh.read()
                data = json.loads(raw)
                text = json.dumps(data, indent=2, ensure_ascii=False)
                return [{"page": 1, "text": text}]
            except json.JSONDecodeError as e:
                logger.debug(f"[KB_WATCH] JSON parse error ({file_path.name}): {e}")
            except Exception as e:
                logger.debug(f"[KB_WATCH] JSON read error ({file_path.name}): {e}")
            return []

        elif suffix == '.csv':
            try:
                text = file_path.read_text(encoding='utf-8', errors='replace')
                return [{"page": 1, "text": text}]
            except Exception:
                return []

        elif suffix == '.docx':
            try:
                import docx
                doc = docx.Document(str(file_path))
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                if text.strip():
                    return [{"page": 1, "text": text.strip()}]
            except ImportError:
                logger.warning("[KB_WATCH] python-docx not installed for .docx support")
            except Exception as e:
                logger.error(f"[KB_WATCH] DOCX read error ({file_path.name}): {e}")
            return []

        else:
            # Try reading as plain text
            try:
                text = file_path.read_text(encoding='utf-8', errors='replace')
                if text.strip() and len(text) < 10_000_000:  # 10MB max
                    return [{"page": 1, "text": text.strip()}]
            except Exception:
                pass
            return []


class ChunkIndexer:
    """
    Chunks documents and maintains a local search index.
    Uses TF-IDF for fast local search (no external dependencies needed).
    Optionally uses sentence-transformers for semantic search if available.
    """

    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.chunks_file = index_dir / "chunks.json"
        self.manifest_file = index_dir / "manifest.json"

        # Load existing index
        self.chunks: List[Dict[str, Any]] = []
        self.manifest: Dict[str, Dict[str, Any]] = {}
        self._load_index()

        # Sentence transformer for semantic search (optional)
        self._embedder = None
        self._embeddings = None
        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("[KB_WATCH] Semantic search enabled (all-MiniLM-L6-v2)")
        except Exception:
            logger.info("[KB_WATCH] Using keyword search (install sentence-transformers for semantic)")

    def _load_index(self):
        """Load existing index from disk."""
        if self.chunks_file.exists():
            try:
                self.chunks = json.loads(self.chunks_file.read_text(encoding='utf-8'))
                logger.info(f"[KB_WATCH] Loaded {len(self.chunks)} existing chunks")
            except Exception as e:
                logger.warning(f"[KB_WATCH] Failed to load chunks: {e}")
                self.chunks = []

        if self.manifest_file.exists():
            try:
                self.manifest = json.loads(self.manifest_file.read_text(encoding='utf-8'))
                logger.info(f"[KB_WATCH] Loaded manifest ({len(self.manifest)} documents)")
            except Exception:
                self.manifest = {}

    def _save_index(self):
        """Save index to disk."""
        try:
            self.chunks_file.write_text(
                json.dumps(self.chunks, ensure_ascii=False, indent=1),
                encoding='utf-8'
            )
            self.manifest_file.write_text(
                json.dumps(self.manifest, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            # Invalidate cached embeddings
            self._embeddings = None
        except Exception as e:
            logger.error(f"[KB_WATCH] Failed to save index: {e}")

    def add_document(self, file_path: str, pages: List[Dict[str, Any]], file_hash: str) -> int:
        """
        Chunk and index a document.
        Returns number of chunks added.
        """
        # Remove old chunks from this file if re-indexing
        self.chunks = [c for c in self.chunks if c.get('source') != file_path]

        chunk_count = 0
        for page_data in pages:
            page_num = page_data.get('page', 1)
            text = page_data.get('text', '')

            # Split into chunks (~500 chars each with overlap)
            page_chunks = self._chunk_text(text, chunk_size=500, overlap=50)
            for i, chunk_text in enumerate(page_chunks):
                self.chunks.append({
                    'text': chunk_text,
                    'source': file_path,
                    'page': page_num,
                    'chunk_idx': i,
                    'indexed_at': datetime.now().isoformat(),
                })
                chunk_count += 1

        # Update manifest
        self.manifest[file_path] = {
            'hash': file_hash,
            'chunks': chunk_count,
            'indexed_at': datetime.now().isoformat(),
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        }

        self._save_index()
        return chunk_count

    def remove_document(self, file_path: str):
        """Remove a document from the index."""
        self.chunks = [c for c in self.chunks if c.get('source') != file_path]
        self.manifest.pop(file_path, None)
        self._save_index()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for relevant chunks."""
        if not self.chunks:
            return []

        if self._embedder is not None:
            return self._semantic_search(query, top_k)
        else:
            return self._keyword_search(query, top_k)

    def _semantic_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search using sentence embeddings."""
        try:
            import numpy as np

            # Compute embeddings (cache them)
            if self._embeddings is None:
                texts = [c['text'] for c in self.chunks]
                self._embeddings = self._embedder.encode(texts, show_progress_bar=False)

            query_emb = self._embedder.encode([query], show_progress_bar=False)
            # Cosine similarity
            scores = np.dot(self._embeddings, query_emb.T).flatten()
            top_indices = np.argsort(scores)[::-1][:top_k]

            results = []
            for idx in top_indices:
                if scores[idx] > 0.1:  # Minimum relevance threshold
                    chunk = self.chunks[idx].copy()
                    chunk['score'] = float(scores[idx])
                    results.append(chunk)
            return results

        except Exception as e:
            logger.warning(f"[KB_WATCH] Semantic search error: {e}")
            return self._keyword_search(query, top_k)

    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Simple keyword-based search."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for chunk in self.chunks:
            text_lower = chunk['text'].lower()
            # Score: count of query words found + exact phrase bonus
            word_hits = sum(1 for w in query_words if w in text_lower)
            phrase_bonus = 5 if query_lower in text_lower else 0
            score = word_hits + phrase_bonus
            if score > 0:
                result = chunk.copy()
                result['score'] = score
                scored.append(result)

        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            # Try to break at sentence boundary
            if end < len(text):
                for sep in ['. ', '.\n', '\n\n', '\n', ' ']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'total_chunks': len(self.chunks),
            'total_documents': len(self.manifest),
            'semantic_search': self._embedder is not None,
            'index_dir': str(self.index_dir),
        }


class KnowledgeWatcher:
    """
    Watches Knowledge Base folders for new/modified files and auto-indexes them.
    
    Monitoring strategy:
    - Polls every N seconds (works on all OS, no watchdog dependency needed)
    - Tracks file hashes to detect changes
    - Processes files in background thread
    - Thread-safe for concurrent access
    """

    SUPPORTED_EXTENSIONS = {
        '.pdf', '.txt', '.md', '.rst', '.json', '.csv', '.docx',
        '.log', '.html', '.xml', '.yaml', '.yml',
    }

    def __init__(self, base_dir: Path = None, poll_interval: float = 5.0):
        if base_dir is None:
            try:
                from config.settings import config
                base_dir = Path(str(config.BASE_DIR))
            except Exception:
                base_dir = Path(".")

        self.base_dir = base_dir
        self.poll_interval = poll_interval

        # Watch directories
        self.watch_dirs = [
            base_dir / "data" / "Monica_Knowledge_Base",
            base_dir / "data" / "monica_knowledge",
            base_dir / "data" / "research_cache",
        ]

        # Ensure directories exist
        for d in self.watch_dirs:
            d.mkdir(parents=True, exist_ok=True)

        # Index storage
        index_dir = base_dir / "data" / "knowledge_index"
        self.extractor = TextExtractor()
        self.indexer = ChunkIndexer(index_dir)

        # State
        self._file_hashes: Dict[str, str] = {}  # path -> hash
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Callbacks
        self.on_document_added: List[Callable[[str, int], None]] = []  # (path, chunks)
        self.on_document_removed: List[Callable[[str], None]] = []

        # Load known hashes from manifest
        for path, info in self.indexer.manifest.items():
            self._file_hashes[path] = info.get('hash', '')

        logger.info(f"[KB_WATCH] Knowledge Watcher initialized")
        logger.info(f"[KB_WATCH] Watching: {[str(d) for d in self.watch_dirs]}")
        logger.info(f"[KB_WATCH] Index: {self.indexer.get_stats()}")

    def start(self):
        """Start watching for file changes in background."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True, name="KB_Watcher")
        self._thread.start()
        logger.info("[KB_WATCH] File watcher started")

    def stop(self):
        """Stop watching."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("[KB_WATCH] File watcher stopped")

    def _watch_loop(self):
        """Main polling loop."""
        # Initial scan
        self._scan_all()

        while self._running:
            try:
                time.sleep(self.poll_interval)
                self._scan_all()
            except Exception as e:
                logger.error(f"[KB_WATCH] Watch loop error: {e}")
                time.sleep(10)

    def _scan_all(self):
        """Scan all watched directories for changes."""
        current_files = set()

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue
            for file_path in watch_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                    continue
                if '__pycache__' in str(file_path):
                    continue

                str_path = str(file_path)
                current_files.add(str_path)

                # Check if new or modified
                file_hash = self._compute_hash(file_path)
                if str_path not in self._file_hashes or self._file_hashes[str_path] != file_hash:
                    self._process_file(file_path, file_hash)

        # Check for removed files
        with self._lock:
            known = set(self._file_hashes.keys())
            removed = known - current_files
            for path in removed:
                logger.info(f"[KB_WATCH] File removed: {Path(path).name}")
                self.indexer.remove_document(path)
                del self._file_hashes[path]
                for cb in self.on_document_removed:
                    try:
                        cb(path)
                    except Exception:
                        pass

    def _process_file(self, file_path: Path, file_hash: str):
        """Extract, chunk, and index a single file."""
        try:
            logger.info(f"[KB_WATCH] Processing: {file_path.name} ({file_path.stat().st_size / 1024:.1f} KB)")

            pages = self.extractor.extract(file_path)
            if not pages:
                logger.warning(f"[KB_WATCH] No text extracted from: {file_path.name}")
                return

            str_path = str(file_path)
            chunk_count = self.indexer.add_document(str_path, pages, file_hash)

            with self._lock:
                self._file_hashes[str_path] = file_hash

            logger.info(f"[KB_WATCH] Indexed: {file_path.name} -> {chunk_count} chunks")

            # Notify callbacks
            for cb in self.on_document_added:
                try:
                    cb(str_path, chunk_count)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"[KB_WATCH] Failed to process {file_path.name}: {e}")

    @staticmethod
    def _compute_hash(file_path: Path) -> str:
        """Compute SHA-256 hash of file for change detection."""
        try:
            h = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(8192), b''):
                    h.update(block)
            return h.hexdigest()[:16]  # First 16 chars is enough
        except Exception:
            return ''

    def force_reindex(self, file_path: str = None):
        """Force re-index a specific file or all files."""
        if file_path:
            p = Path(file_path)
            if p.exists():
                self._process_file(p, self._compute_hash(p))
        else:
            logger.info("[KB_WATCH] Force re-indexing all files...")
            self._file_hashes.clear()
            self.indexer.chunks.clear()
            self.indexer.manifest.clear()
            self._scan_all()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        return self.indexer.search(query, top_k)

    def get_context(self, query: str, top_k: int = 5) -> str:
        """Get formatted context for AI prompts."""
        results = self.search(query, top_k)
        if not results:
            return ""
        lines = ["[KNOWLEDGE_BASE]"]
        for r in results:
            src = Path(r.get('source', '')).name
            page = r.get('page', '')
            score = r.get('score', 0)
            text = r.get('text', '')
            lines.append(f"(score={score:.2f}) {src} p.{page}:\n{text}")
        lines.append("[/KNOWLEDGE_BASE]")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get watcher and index statistics."""
        stats = self.indexer.get_stats()
        stats['watched_dirs'] = [str(d) for d in self.watch_dirs]
        stats['tracked_files'] = len(self._file_hashes)
        stats['running'] = self._running
        return stats


# Singleton
_watcher = None


def get_knowledge_watcher() -> KnowledgeWatcher:
    """Get or create the knowledge watcher singleton."""
    global _watcher
    if _watcher is None:
        _watcher = KnowledgeWatcher()
    return _watcher
