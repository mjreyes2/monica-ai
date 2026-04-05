"""
RAG (Retrieval Augmented Generation) System for MaxOne Drive (D:)
Allows Monica to search and retrieve information from your D: drive documents.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading
import pickle

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_SENTENCE_TRANSFORMERS = True
except Exception as e:
    SentenceTransformer = None  # type: ignore
    HAS_SENTENCE_TRANSFORMERS = False
    print(f"[MAXONE-RAG] sentence-transformers not available: {e}")
    print("[MAXONE-RAG] If this is an EncoderDecoderCache/transformers.trainer error, align transformers + peft versions.")


class MaxOneDriveRAG:
    """
    RAG system for MaxOne Drive (D:) - allows Monica to search your documents.

    Features:
    - Automatic document indexing (PDF, DOCX, TXT, MD, etc.)
    - Semantic search using embeddings
    - Persistent index caching for fast startup
    - Background indexing to avoid blocking
    """

    def __init__(self, drive_path: str = "D:/", cache_dir: str = "data/maxone_drive_index"):
        """
        Initialize MaxOne Drive RAG system.

        Args:
            drive_path: Path to your MaxOne Drive (default: D:/)
            cache_dir: Directory to store index cache
        """
        self.drive_path = Path(drive_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Index storage
        self.documents = []  # List of {path, content, metadata}
        self.embeddings = None
        self.model = None
        self.is_loaded = False
        self.is_indexing = False

        # Supported file types
        self.supported_extensions = {
            '.txt', '.md', '.pdf', '.docx', '.doc',
            '.csv', '.json', '.py', '.js', '.html',
            '.xml', '.yaml', '.yml', '.log', '.rtf'
        }

        # Index files
        self.docs_file = self.cache_dir / "documents.pkl"
        self.embeddings_file = self.cache_dir / "embeddings.npy"
        self.metadata_file = self.cache_dir / "metadata.json"

        print(f"[MAXONE-RAG] Initialized for drive: {self.drive_path}")

        # Try to load existing index
        if self._load_cache():
            print(f"[MAXONE-RAG] Loaded cached index ({len(self.documents)} documents)")
            self.is_loaded = True
        else:
            print(f"[MAXONE-RAG] No cache found. Run build_index() to create index.")

    def _load_cache(self) -> bool:
        """Load cached index from disk."""
        try:
            if not (self.docs_file.exists() and self.embeddings_file.exists()):
                return False

            # Load documents
            with open(self.docs_file, 'rb') as f:
                self.documents = pickle.load(f)

            # Load embeddings
            import numpy as np
            self.embeddings = np.load(self.embeddings_file)

            # Load embedding model (lightweight)
            if HAS_SENTENCE_TRANSFORMERS:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, 22MB model

            return True
        except Exception as e:
            print(f"[MAXONE-RAG] Cache load failed: {e}")
            return False

    def _save_cache(self):
        """Save index to disk for fast loading."""
        try:
            # Save documents
            with open(self.docs_file, 'wb') as f:
                pickle.dump(self.documents, f)

            # Save embeddings
            import numpy as np
            np.save(self.embeddings_file, self.embeddings)

            # Save metadata
            metadata = {
                'num_documents': len(self.documents),
                'indexed_paths': [str(doc['path']) for doc in self.documents[:100]],  # First 100
                'file_types': list(self.supported_extensions)
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"[MAXONE-RAG] Index cached ({len(self.documents)} documents)")
        except Exception as e:
            print(f"[MAXONE-RAG] Cache save failed: {e}")

    def build_index(self, max_files: int = 10000, background: bool = True):
        """
        Build search index from D: drive documents.

        Args:
            max_files: Maximum number of files to index
            background: If True, run indexing in background thread
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            print("[MAXONE-RAG] Cannot build index: sentence-transformers not installed")
            print("Install with: pip install sentence-transformers")
            return

        if self.is_indexing:
            print("[MAXONE-RAG] Indexing already in progress")
            return

        def _index():
            try:
                self.is_indexing = True
                print(f"[MAXONE-RAG] Starting index build from {self.drive_path}")

                # Load model
                print("[MAXONE-RAG] Loading embedding model (all-MiniLM-L6-v2)...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')

                # Find files
                print(f"[MAXONE-RAG] Scanning drive for supported files...")
                file_paths = []

                for root, dirs, files in os.walk(self.drive_path):
                    # Skip system folders
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['$RECYCLE.BIN', 'System Volume Information']]

                    for file in files:
                        if len(file_paths) >= max_files:
                            break

                        file_path = Path(root) / file
                        if file_path.suffix.lower() in self.supported_extensions:
                            file_paths.append(file_path)

                    if len(file_paths) >= max_files:
                        break

                print(f"[MAXONE-RAG] Found {len(file_paths)} files to index")

                # Extract text and create documents
                self.documents = []
                for i, file_path in enumerate(file_paths):
                    if i % 100 == 0:
                        print(f"[MAXONE-RAG] Processing {i}/{len(file_paths)}...")

                    try:
                        content = self._extract_text(file_path)
                        if content:
                            self.documents.append({
                                'path': str(file_path),
                                'content': content[:5000],  # First 5000 chars
                                'filename': file_path.name,
                                'extension': file_path.suffix,
                                'size': file_path.stat().st_size
                            })
                    except Exception as e:
                        # Skip files that can't be read
                        pass

                print(f"[MAXONE-RAG] Successfully processed {len(self.documents)} documents")

                # Create embeddings
                print("[MAXONE-RAG] Generating embeddings...")
                texts = [doc['content'] for doc in self.documents]
                self.embeddings = self.model.encode(texts, show_progress_bar=True)

                # Save cache
                self._save_cache()

                self.is_loaded = True
                print(f"[MAXONE-RAG] ✅ Index build complete! ({len(self.documents)} documents)")

            except Exception as e:
                print(f"[MAXONE-RAG] Index build failed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.is_indexing = False

        if background:
            thread = threading.Thread(target=_index, daemon=True)
            thread.start()
            print("[MAXONE-RAG] Indexing started in background...")
        else:
            _index()

    def _extract_text(self, file_path: Path) -> str:
        """Extract text from a file based on its type."""
        ext = file_path.suffix.lower()

        try:
            # Plain text files
            if ext in {'.txt', '.md', '.py', '.js', '.html', '.xml', '.json', '.yaml', '.yml', '.csv', '.log'}:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

            # PDF files
            elif ext == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages[:10]:  # First 10 pages
                            text += page.extract_text()
                        return text
                except:
                    return ""

            # Word documents
            elif ext in {'.docx', '.doc'}:
                try:
                    from docx import Document
                    doc = Document(file_path)
                    return "\n".join([para.text for para in doc.paragraphs])
                except:
                    return ""

            # RTF files
            elif ext == '.rtf':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

            return ""

        except Exception:
            return ""

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using semantic search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of matching documents with scores
        """
        if not self.is_loaded:
            return []

        if not HAS_SENTENCE_TRANSFORMERS or self.model is None:
            return []

        try:
            # Encode query
            query_embedding = self.model.encode([query])[0]

            # Calculate cosine similarity
            import numpy as np
            scores = np.dot(self.embeddings, query_embedding)

            # Get top-k results
            top_indices = np.argsort(scores)[-top_k:][::-1]

            results = []
            for idx in top_indices:
                results.append({
                    'path': self.documents[idx]['path'],
                    'filename': self.documents[idx]['filename'],
                    'content': self.documents[idx]['content'][:500],  # First 500 chars for preview
                    'score': float(scores[idx]),
                    'extension': self.documents[idx]['extension']
                })

            return results

        except Exception as e:
            print(f"[MAXONE-RAG] Search error: {e}")
            return []

    def get_context(self, query: str, top_k: int = 3) -> str:
        """
        Get formatted context for Monica's response.

        Args:
            query: Search query
            top_k: Number of results to include

        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=top_k)

        if not results:
            return ""

        lines = ["[MAXONE_DRIVE_CONTEXT]"]
        lines.append(f"Found {len(results)} relevant documents from your MaxOne Drive (D:):\n")

        for i, result in enumerate(results, 1):
            lines.append(f"{i}. {result['filename']} (score: {result['score']:.3f})")
            lines.append(f"   Path: {result['path']}")
            lines.append(f"   Content preview: {result['content'][:300]}...")
            lines.append("")

        lines.append("[/MAXONE_DRIVE_CONTEXT]")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        if not self.is_loaded:
            return {
                'status': 'not_loaded',
                'num_documents': 0
            }

        return {
            'status': 'loaded',
            'num_documents': len(self.documents),
            'drive_path': str(self.drive_path),
            'cache_dir': str(self.cache_dir),
            'supported_extensions': list(self.supported_extensions)
        }


# Convenience function for quick usage
def create_maxone_rag(rebuild: bool = False) -> MaxOneDriveRAG:
    """
    Create MaxOne Drive RAG system.

    Args:
        rebuild: If True, rebuild the index even if cache exists

    Returns:
        MaxOneDriveRAG instance
    """
    rag = MaxOneDriveRAG()

    if not rag.is_loaded or rebuild:
        print("[MAXONE-RAG] Building index...")
        rag.build_index(background=True)

    return rag
