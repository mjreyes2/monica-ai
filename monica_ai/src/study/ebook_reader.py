"""
Monica Ebook Reader
Reads and searches through ebooks on local drives (Maxone Drive D:, external drive, etc.)
Supports PDF, EPUB, TXT, and other common ebook formats.

Author: Monica AI
Date: December 2025
"""

import os
import re
import json
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

# PDF support
HAS_PYPDF = False
try:
    import pypdf
    HAS_PYPDF = True
    print("[OK] PyPDF loaded for PDF reading")
except ImportError:
    try:
        import PyPDF2 as pypdf
        HAS_PYPDF = True
        print("[OK] PyPDF2 loaded for PDF reading")
    except ImportError:
        print("[WARNING] PDF support not available - install pypdf or PyPDF2")

# EPUB support
HAS_EPUB = False
try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    HAS_EPUB = True
    print("[OK] EbookLib loaded for EPUB reading")
except ImportError:
    print("[WARNING] EPUB support not available - install ebooklib beautifulsoup4")

# DOCX support
HAS_DOCX = False
try:
    import docx
    HAS_DOCX = True
    print("[OK] python-docx loaded for DOCX reading")
except ImportError:
    pass


@dataclass
class Ebook:
    """Represents an ebook file."""
    path: Path
    title: str
    format: str
    size_mb: float
    last_modified: str
    
    @classmethod
    def from_path(cls, path: Path) -> 'Ebook':
        """Create Ebook from file path."""
        stat = path.stat()
        return cls(
            path=path,
            title=path.stem,
            format=path.suffix.lower(),
            size_mb=stat.st_size / (1024 * 1024),
            last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
        )


@dataclass
class SearchResult:
    """A search result from an ebook."""
    book_title: str
    book_path: str
    page_or_chapter: str
    context: str
    relevance_score: float


class EbookReader:
    """
    Reads and searches through ebooks on local drives.
    """
    
    # Supported ebook formats
    SUPPORTED_FORMATS = ['.pdf', '.epub', '.txt', '.md', '.docx', '.doc', '.rtf', '.html', '.htm']
    
    def __init__(self, library_paths: List[str] = None):
        """
        Initialize the ebook reader.
        
        Args:
            library_paths: List of paths to scan for ebooks
        """
        # Default library paths
        self.library_paths = []
        
        if library_paths:
            self.library_paths.extend(library_paths)
        
        # Add common ebook locations
        default_paths = [
            "D:/",  # Maxone Drive
            "D:/ebooks",
            "D:/Books",
            "D:/Documents",
            os.path.expanduser("~/Documents/Books"),
            os.path.expanduser("~/Documents/ebooks"),
        ]
        
        for path in default_paths:
            if os.path.exists(path) and path not in self.library_paths:
                self.library_paths.append(path)
        
        # Cache of discovered ebooks
        self.ebook_cache: Dict[str, Ebook] = {}
        self.cache_file = Path(__file__).parent.parent.parent / "data" / "ebook_cache.json"
        self.cache_file.parent.mkdir(exist_ok=True)
        
        # Text cache for faster searching
        self.text_cache: Dict[str, str] = {}
        
        # Load cache
        self._load_cache()
        
        print(f"[EBOOK] Reader initialized with {len(self.library_paths)} library paths")
        print(f"[EBOOK] Found {len(self.ebook_cache)} cached ebooks")
    
    def _load_cache(self):
        """Load ebook cache from file."""
        if self.cache_file.exists():
            try:
                data = json.loads(self.cache_file.read_text(encoding='utf-8', errors='replace'))
                for path, info in data.items():
                    if os.path.exists(path):
                        self.ebook_cache[path] = Ebook(
                            path=Path(path),
                            title=info['title'],
                            format=info['format'],
                            size_mb=info['size_mb'],
                            last_modified=info['last_modified']
                        )
            except Exception as e:
                print(f"[EBOOK] Error loading cache: {e}")
    
    def _save_cache(self):
        """Save ebook cache to file."""
        try:
            data = {}
            for path, ebook in self.ebook_cache.items():
                data[path] = {
                    'title': ebook.title,
                    'format': ebook.format,
                    'size_mb': ebook.size_mb,
                    'last_modified': ebook.last_modified
                }
            self.cache_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"[EBOOK] Error saving cache: {e}")
    
    def scan_libraries(self, max_depth: int = 5) -> int:
        """
        Scan library paths for ebooks.
        
        Returns:
            Number of ebooks found
        """
        count = 0
        
        for library_path in self.library_paths:
            if not os.path.exists(library_path):
                continue
            
            print(f"[EBOOK] Scanning: {library_path}")
            
            for root, dirs, files in os.walk(library_path):
                # Limit depth
                depth = root.replace(library_path, '').count(os.sep)
                if depth > max_depth:
                    continue
                
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.SUPPORTED_FORMATS:
                        filepath = os.path.join(root, file)
                        if filepath not in self.ebook_cache:
                            try:
                                ebook = Ebook.from_path(Path(filepath))
                                self.ebook_cache[filepath] = ebook
                                count += 1
                            except Exception as e:
                                print(f"[EBOOK] Error scanning {filepath}: {e}")
        
        self._save_cache()
        print(f"[EBOOK] Found {count} new ebooks, total: {len(self.ebook_cache)}")
        return count
    
    def list_ebooks(self, format_filter: str = None, search_term: str = None) -> List[Ebook]:
        """
        List available ebooks.
        
        Args:
            format_filter: Filter by format (e.g., '.pdf')
            search_term: Filter by title containing term
        """
        results = []
        
        for ebook in self.ebook_cache.values():
            if format_filter and ebook.format != format_filter:
                continue
            
            if search_term and search_term.lower() not in ebook.title.lower():
                continue
            
            results.append(ebook)
        
        # Sort by title
        results.sort(key=lambda x: x.title.lower())
        return results
    
    def read_ebook(self, path: str, max_chars: int = 50000) -> Optional[str]:
        """
        Read the text content of an ebook.
        
        Args:
            path: Path to the ebook
            max_chars: Maximum characters to return
        """
        # Check cache
        if path in self.text_cache:
            return self.text_cache[path][:max_chars]
        
        path_obj = Path(path)
        if not path_obj.exists():
            return None
        
        ext = path_obj.suffix.lower()
        text = None
        
        try:
            if ext == '.txt' or ext == '.md':
                text = path_obj.read_text(encoding='utf-8', errors='ignore')
            
            elif ext == '.pdf' and HAS_PYPDF:
                text = self._read_pdf(path_obj)
            
            elif ext == '.epub' and HAS_EPUB:
                text = self._read_epub(path_obj)
            
            elif ext == '.docx' and HAS_DOCX:
                text = self._read_docx(path_obj)
            
            elif ext in ['.html', '.htm']:
                text = self._read_html(path_obj)
            
            if text:
                # Cache the text
                self.text_cache[path] = text
                return text[:max_chars]
        
        except Exception as e:
            print(f"[EBOOK] Error reading {path}: {e}")
        
        return None
    
    def _read_pdf(self, path: Path) -> str:
        """Read text from PDF file."""
        text_parts = []
        
        with open(path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages[:100]:  # Limit pages
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return '\n\n'.join(text_parts)
    
    def _read_epub(self, path: Path) -> str:
        """Read text from EPUB file."""
        book = epub.read_epub(str(path))
        text_parts = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text()
                if text.strip():
                    text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    
    def _read_docx(self, path: Path) -> str:
        """Read text from DOCX file."""
        doc = docx.Document(str(path))
        text_parts = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        return '\n\n'.join(text_parts)
    
    def _read_html(self, path: Path) -> str:
        """Read text from HTML file."""
        content = path.read_text(encoding='utf-8', errors='ignore')
        
        # Simple HTML tag removal
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def search_ebooks(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search through all ebooks for a query.
        
        Args:
            query: Search query
            max_results: Maximum number of results
        """
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        for path, ebook in self.ebook_cache.items():
            # First check title
            title_match = query_lower in ebook.title.lower()
            
            # Then search content
            text = self.read_ebook(path, max_chars=100000)
            if not text:
                continue
            
            text_lower = text.lower()
            
            # Find matches
            for i, word in enumerate(query_words):
                pos = text_lower.find(word)
                if pos != -1:
                    # Extract context
                    start = max(0, pos - 100)
                    end = min(len(text), pos + 200)
                    context = text[start:end].strip()
                    
                    # Calculate relevance
                    word_count = sum(1 for w in query_words if w in text_lower)
                    relevance = word_count / len(query_words)
                    
                    if title_match:
                        relevance += 0.5
                    
                    results.append(SearchResult(
                        book_title=ebook.title,
                        book_path=path,
                        page_or_chapter="",
                        context=f"...{context}...",
                        relevance_score=relevance
                    ))
                    break
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]
    
    def find_answer(self, question: str, ai_manager=None) -> str:
        """
        Find an answer to a question using ebook content.
        
        Args:
            question: The question to answer
            ai_manager: AI manager for processing
        """
        # Search for relevant content
        results = self.search_ebooks(question, max_results=5)
        
        if not results:
            return "I couldn't find relevant information in your ebook library. Try scanning for new books or rephrasing your question."
        
        # Gather context from top results
        context_parts = []
        for result in results[:3]:
            context_parts.append(f"From '{result.book_title}':\n{result.context}")
        
        context = "\n\n".join(context_parts)
        
        if ai_manager:
            prompt = f"""Based on the following excerpts from the user's ebook library, answer their question.

QUESTION: {question}

RELEVANT EXCERPTS:
{context}

Provide a helpful answer based on this information. If the excerpts don't fully answer the question, say so and provide what information is available."""

            try:
                return ai_manager.get_response(prompt)
            except:
                pass
        
        # Return raw context if no AI
        return f"Found relevant information:\n\n{context}"
    
    def get_book_summary(self, path: str, ai_manager=None) -> str:
        """Get a summary of an ebook."""
        text = self.read_ebook(path, max_chars=10000)
        
        if not text:
            return "Could not read this ebook."
        
        ebook = self.ebook_cache.get(path)
        title = ebook.title if ebook else Path(path).stem
        
        if ai_manager:
            prompt = f"""Summarize this book excerpt in 3-4 paragraphs:

Title: {title}

Content:
{text[:5000]}

Provide a clear summary of the main topics and key points."""

            try:
                return ai_manager.get_response(prompt)
            except:
                pass
        
        # Return first part of text
        return f"'{title}' begins:\n\n{text[:1000]}..."
    
    def add_library_path(self, path: str) -> bool:
        """Add a new library path."""
        if os.path.exists(path) and path not in self.library_paths:
            self.library_paths.append(path)
            print(f"[EBOOK] Added library path: {path}")
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        formats = {}
        total_size = 0
        
        for ebook in self.ebook_cache.values():
            formats[ebook.format] = formats.get(ebook.format, 0) + 1
            total_size += ebook.size_mb
        
        return {
            'total_books': len(self.ebook_cache),
            'formats': formats,
            'total_size_mb': round(total_size, 2),
            'library_paths': self.library_paths
        }


# Singleton instance
_reader = None

def get_ebook_reader(library_paths: List[str] = None) -> EbookReader:
    """Get or create the ebook reader singleton."""
    global _reader
    if _reader is None:
        _reader = EbookReader(library_paths)
    elif library_paths:
        for path in library_paths:
            _reader.add_library_path(path)
    return _reader


# Test
if __name__ == "__main__":
    print("Ebook Reader Test")
    
    reader = get_ebook_reader(["D:/"])
    
    print("\nLibrary stats:", reader.get_stats())
    
    print("\nScanning for ebooks...")
    count = reader.scan_libraries()
    print(f"Found {count} ebooks")
    
    print("\nListing PDF ebooks:")
    pdfs = reader.list_ebooks(format_filter='.pdf')
    for pdf in pdfs[:5]:
        print(f"  - {pdf.title} ({pdf.size_mb:.1f} MB)")
