"""
Lightweight PDF retriever that loads a prebuilt index from
models/kb_index/<name> and returns top matching chunks. If the index
is missing but a source folder is available, it can auto-build the index
in the background on first use.

Depends on monica_ai.knowledge.pdf_indexer.PDFIndex/build_index
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading

try:
    from monica_ai.knowledge.pdf_indexer import PDFIndex, build_index
    HAS_PDF_INDEX = True
except Exception:
    HAS_PDF_INDEX = False


class PDFRetriever:
    def __init__(self, index_dir: str | Path = "models/kb_index/books_pdf", source_root: Optional[str | Path] = None):
        self.index_dir = Path(index_dir)
        self.source_root = Path(source_root) if source_root else None
        self.idx: Optional[PDFIndex] = None
        self._building = False
        if HAS_PDF_INDEX and self.index_dir.exists():
            try:
                self.idx = PDFIndex.load(self.index_dir)
                print(f"[PDF] Loaded knowledge index: {self.index_dir}")
            except Exception as e:
                print(f"[PDF] Failed to load index: {e}")
                self.idx = None
        else:
            if not HAS_PDF_INDEX:
                print("[PDF] PDFIndex not available (missing dependency)")
            else:
                print(f"[PDF] Index directory not found: {self.index_dir}")
                # Auto-build if a source root exists
                if self.source_root and self.source_root.exists() and not self._building:
                    print(f"[PDF] First-run: auto-building index from {self.source_root} → {self.index_dir}")
                    def _build():
                        try:
                            self._building = True
                            build_index(str(self.source_root), name=self.index_dir.name, out_dir=str(self.index_dir.parent))
                            # Try load after build
                            self.idx = PDFIndex.load(self.index_dir)
                            print(f"[PDF] [OK] Auto-build complete: {self.index_dir}")
                        except Exception as e:
                            print(f"[PDF] Auto-build failed: {e}")
                        finally:
                            self._building = False
                    threading.Thread(target=_build, daemon=True).start()

    def is_ready(self) -> bool:
        return self.idx is not None

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.idx:
            return []
        try:
            return self.idx.search(query, top_k=top_k)
        except Exception as e:
            print(f"[PDF] Retrieval error: {e}")
            return []

    def get_context(self, query: str, top_k: int = 5) -> str:
        """Return a formatted CONTEXT block for prompts."""
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""
        lines = ["[PDF_CONTEXT]"]
        for r in results:
            src = r.get("source", "")
            page = r.get("page", "")
            score = r.get("score", 0.0)
            text = r.get("text", "")
            lines.append(f"(score={score:.3f}) Source: {src} (p.{page})\n{text}")
        lines.append("[/PDF_CONTEXT]")
        return "\n".join(lines)
