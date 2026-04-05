"""
Monica AI - Knowledge Base Manager
Consolidates all knowledge sources into a single access point.

Knowledge hierarchy:
1. data/Monica_Knowledge_Base/  - Primary KB (Textbooks + domain folders)
2. data/monica_knowledge/       - Runtime learned knowledge (merged into #1)
3. src/ai/knowledge_cache/      - Cached search results
4. models/kb_index/             - Pre-built PDF search indexes

The two visible KB folders serve different purposes:
- Monica_Knowledge_Base: STATIC reference library (PDFs, domain data)
- monica_knowledge: DYNAMIC runtime knowledge (learned facts, people memory)
Both are accessed through this unified manager.
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("Monica.KnowledgeBase")


class KnowledgeBaseManager:
    """Unified access to all of Monica's knowledge sources."""

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            try:
                from config.settings import config
                base_dir = Path(str(config.BASE_DIR))
            except Exception:
                base_dir = Path(".")

        self.base_dir = base_dir

        # Primary knowledge base (static reference library)
        self.static_kb_dir = base_dir / "data" / "Monica_Knowledge_Base"
        # Runtime learned knowledge
        self.dynamic_kb_dir = base_dir / "data" / "monica_knowledge"
        # PDF index directory
        self.index_dir = base_dir / "models" / "kb_index"
        # Cache directory
        self.cache_dir = base_dir / "src" / "ai" / "knowledge_cache"

        # Ensure directories exist
        for d in [self.dynamic_kb_dir, self.cache_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Load domain index
        self.domain_index = self._load_domain_index()
        self.pdf_retriever = None

        logger.info(f"KnowledgeBaseManager initialized")
        logger.info(f"  Static KB: {self.static_kb_dir} (exists={self.static_kb_dir.exists()})")
        logger.info(f"  Dynamic KB: {self.dynamic_kb_dir}")
        logger.info(f"  Domains: {len(self.domain_index)} indexed")

    def _load_domain_index(self) -> Dict[str, Any]:
        """Load the domain index that maps topics to PDF categories."""
        idx_file = self.static_kb_dir / "domain_index.json"
        if idx_file.exists():
            try:
                with open(idx_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load domain index: {e}")
        return {}

    def get_pdf_retriever(self):
        """Get or create the PDF retriever (lazy init)."""
        if self.pdf_retriever is None:
            try:
                from ai.pdf_retriever import PDFRetriever
                self.pdf_retriever = PDFRetriever()
                logger.info(f"PDF Retriever initialized (ready={self.pdf_retriever.is_ready()})")
            except Exception as e:
                logger.warning(f"PDF Retriever not available: {e}")
        return self.pdf_retriever

    def get_books_pdf_dir(self) -> Optional[Path]:
        """Get the Textbooks directory path (formerly Books PDF)."""
        books_dir = self.static_kb_dir / "Textbooks"
        return books_dir if books_dir.exists() else None

    def list_knowledge_domains(self) -> List[str]:
        """List all available knowledge domains from the static KB."""
        if not self.static_kb_dir.exists():
            return []
        domains = []
        for item in sorted(self.static_kb_dir.iterdir()):
            if item.is_dir() and item.name != "__pycache__":
                domains.append(item.name)
        return domains

    def count_resources(self) -> Dict[str, int]:
        """Count all knowledge resources."""
        counts = {"domains": 0, "pdf_files": 0, "learned_facts": 0, "people_known": 0}

        # Count domains
        if self.static_kb_dir.exists():
            counts["domains"] = len([d for d in self.static_kb_dir.iterdir() if d.is_dir()])

        # Count PDFs
        books_dir = self.get_books_pdf_dir()
        if books_dir:
            counts["pdf_files"] = len(list(books_dir.rglob("*.pdf")))

        # Count learned facts
        knowledge_file = self.dynamic_kb_dir / "knowledge.json"
        if knowledge_file.exists():
            try:
                with open(knowledge_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for category, items in data.items():
                    if isinstance(items, list):
                        counts["learned_facts"] += len(items)
            except Exception:
                pass

        # Count people
        people_file = self.dynamic_kb_dir / "people_memory.json"
        if people_file.exists():
            try:
                with open(people_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                counts["people_known"] = len(data)
            except Exception:
                pass

        return counts

    def search_pdfs(self, query: str, top_k: int = 5) -> str:
        """Search the PDF knowledge base."""
        retriever = self.get_pdf_retriever()
        if retriever and retriever.is_ready():
            return retriever.get_context(query, top_k=top_k)
        return ""

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base status."""
        counts = self.count_resources()
        return {
            "static_kb_exists": self.static_kb_dir.exists(),
            "static_kb_path": str(self.static_kb_dir),
            "dynamic_kb_exists": self.dynamic_kb_dir.exists(),
            "dynamic_kb_path": str(self.dynamic_kb_dir),
            "domains": self.list_knowledge_domains(),
            "resources": counts,
            "pdf_index_ready": self.pdf_retriever.is_ready() if self.pdf_retriever else False,
        }


# Singleton
_kb_manager = None


def get_knowledge_base_manager() -> KnowledgeBaseManager:
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager()
    return _kb_manager
