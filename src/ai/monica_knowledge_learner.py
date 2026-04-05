"""
Monica AI - Knowledge Learner

Gives Monica the ability to:
1. Read and remember content from URLs (websites, articles)
2. Remember information the user reads aloud / tells her
3. Store learned knowledge in the dynamic knowledge base
4. Recall learned knowledge when relevant to conversation

All learned knowledge is persisted to:
  data/monica_knowledge/learned_knowledge.json

Usage:
    from ai.monica_knowledge_learner import get_knowledge_learner
    learner = get_knowledge_learner()
    learner.learn_from_url("https://example.com/article")
    learner.learn_from_spoken("The mitochondria is the powerhouse of the cell")
    context = learner.get_relevant_knowledge("tell me about mitochondria")
"""

import json
import logging
import re
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger("Monica.KnowledgeLearner")


class MonicaKnowledgeLearner:
    """Learns and remembers knowledge from URLs, spoken info, and PDFs."""

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            try:
                from config.settings import config
                base_dir = Path(str(config.BASE_DIR))
            except Exception:
                base_dir = Path(".")

        self.base_dir = base_dir
        self.knowledge_dir = base_dir / "data" / "monica_knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        self.knowledge_file = self.knowledge_dir / "learned_knowledge.json"
        self.url_cache_dir = self.knowledge_dir / "url_cache"
        self.url_cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing knowledge
        self.knowledge: Dict[str, Any] = self._load_knowledge()
        logger.info(f"KnowledgeLearner: {len(self.knowledge.get('entries', []))} learned entries, "
                     f"{len(self.knowledge.get('urls_read', []))} URLs read")

    def _load_knowledge(self) -> Dict[str, Any]:
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load knowledge: {e}")
        return {
            "entries": [],
            "urls_read": [],
            "spoken_facts": [],
            "created_at": datetime.now().isoformat(),
        }

    def _save_knowledge(self):
        try:
            with open(self.knowledge_file, "w", encoding="utf-8") as f:
                json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}")

    # ==================== URL Reading ====================

    def learn_from_url(self, url: str) -> str:
        """
        Read a URL, extract text content, and store it in the knowledge base.
        Returns a summary of what was learned.
        """
        logger.info(f"Learning from URL: {url}")

        # Extract text from URL
        text = self._fetch_url_text(url)
        if not text:
            return f"I couldn't read the content from {url}. The page may be blocked or empty."

        # Chunk and store
        chunks = self._chunk_text(text, chunk_size=800, overlap=100)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

        entry = {
            "type": "url",
            "source": url,
            "hash": url_hash,
            "title": self._extract_title(text),
            "num_chunks": len(chunks),
            "total_chars": len(text),
            "learned_at": datetime.now().isoformat(),
            "chunks": chunks[:50],  # Keep up to 50 chunks per URL
        }

        # Remove old entry for same URL if re-reading
        self.knowledge["entries"] = [
            e for e in self.knowledge["entries"] if e.get("source") != url
        ]
        self.knowledge["entries"].append(entry)

        # Track URL
        if url not in self.knowledge["urls_read"]:
            self.knowledge["urls_read"].append(url)

        self._save_knowledge()
        self._index_in_watcher(chunks, url)

        title = entry["title"] or url
        summary = f"I've read and memorized the content from '{title}'. "
        summary += f"Stored {len(chunks)} knowledge chunks ({len(text):,} characters). "
        summary += "I'll remember this information for future conversations."
        logger.info(summary)
        return summary

    def _fetch_url_text(self, url: str) -> Optional[str]:
        """Fetch and extract readable text from a URL."""
        try:
            import urllib.request
            import urllib.error

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()

                # Handle encoding
                encoding = "utf-8"
                if "charset=" in content_type:
                    encoding = content_type.split("charset=")[-1].split(";")[0].strip()
                try:
                    html = raw.decode(encoding, errors="replace")
                except (UnicodeDecodeError, LookupError):
                    html = raw.decode("utf-8", errors="replace")

                # If it's a PDF, try to save and extract
                if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
                    return self._extract_pdf_from_bytes(raw, url)

                # Extract text from HTML
                return self._html_to_text(html)

        except Exception as e:
            logger.error(f"URL fetch error: {e}")
            return None

    def _html_to_text(self, html: str) -> str:
        """Extract readable text from HTML."""
        # Try BeautifulSoup first
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Remove script, style, nav, footer
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            # Clean up whitespace
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines)
        except ImportError:
            pass

        # Fallback: regex-based HTML stripping
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&#\d+;", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _extract_pdf_from_bytes(self, pdf_bytes: bytes, source: str) -> Optional[str]:
        """Extract text from PDF bytes."""
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            texts = []
            for page in doc:
                text = page.get_text("text")
                if text.strip():
                    texts.append(text.strip())
            doc.close()
            return "\n\n".join(texts) if texts else None
        except Exception as e:
            logger.debug(f"PDF extraction error: {e}")
            return None

    def _extract_title(self, text: str) -> Optional[str]:
        """Try to extract a title from text."""
        lines = text.strip().split("\n")
        for line in lines[:5]:
            line = line.strip()
            if 10 < len(line) < 200 and not line.startswith("http"):
                return line
        return None

    # ==================== Spoken Info ====================

    def learn_from_spoken(self, text: str, topic: str = None) -> str:
        """
        Remember something the user told Monica or read aloud.
        This is for when the user says things like:
        - "Remember this: the formula for force is F=ma"
        - "I'm reading from my textbook: [content]"
        - Any factual information the user shares
        """
        if not text or len(text.strip()) < 10:
            return "That's too short for me to store. Could you tell me more?"

        entry = {
            "type": "spoken",
            "content": text.strip(),
            "topic": topic,
            "learned_at": datetime.now().isoformat(),
            "char_count": len(text),
        }

        self.knowledge["spoken_facts"].append(entry)
        # Keep last 500 spoken facts
        self.knowledge["spoken_facts"] = self.knowledge["spoken_facts"][-500:]

        # Also store as a knowledge entry for search
        chunks = self._chunk_text(text, chunk_size=500, overlap=50)
        knowledge_entry = {
            "type": "spoken",
            "source": f"User told me on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "title": topic or self._extract_title(text) or "Spoken information",
            "num_chunks": len(chunks),
            "total_chars": len(text),
            "learned_at": datetime.now().isoformat(),
            "chunks": chunks,
        }
        self.knowledge["entries"].append(knowledge_entry)

        self._save_knowledge()
        self._index_in_watcher(chunks, f"spoken:{datetime.now().isoformat()}")

        return f"Got it, I've memorized that information ({len(text)} characters). I'll remember it."

    # ==================== Knowledge Retrieval ====================

    def get_relevant_knowledge(self, query: str, top_k: int = 3) -> str:
        """Search learned knowledge for content relevant to a query."""
        if not self.knowledge.get("entries"):
            return ""

        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_chunks = []
        for entry in self.knowledge["entries"]:
            source = entry.get("source", "unknown")
            title = entry.get("title", "")

            for chunk in entry.get("chunks", []):
                chunk_lower = chunk.lower()
                # Score: keyword hits + title match + phrase match
                word_hits = sum(1 for w in query_words if w in chunk_lower and len(w) > 2)
                title_bonus = 3 if any(w in (title or "").lower() for w in query_words if len(w) > 2) else 0
                phrase_bonus = 5 if query_lower[:30] in chunk_lower else 0
                score = word_hits + title_bonus + phrase_bonus

                if score > 0:
                    scored_chunks.append({
                        "text": chunk,
                        "source": source,
                        "title": title,
                        "score": score,
                    })

        if not scored_chunks:
            return ""

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        top = scored_chunks[:top_k]

        parts = ["[LEARNED KNOWLEDGE - Monica has memorized this information]"]
        for item in top:
            src = item.get("title") or item.get("source", "")
            parts.append(f"From: {src}")
            parts.append(item["text"][:500])
            parts.append("")
        parts.append("[/LEARNED KNOWLEDGE]")
        return "\n".join(parts)

    def get_context_for_prompt(self, user_text: str) -> str:
        """Get learned knowledge context to inject into AI prompts."""
        return self.get_relevant_knowledge(user_text, top_k=3)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self.knowledge.get("entries", [])),
            "urls_read": len(self.knowledge.get("urls_read", [])),
            "spoken_facts": len(self.knowledge.get("spoken_facts", [])),
            "total_chunks": sum(len(e.get("chunks", [])) for e in self.knowledge.get("entries", [])),
        }

    # ==================== Indexing into KnowledgeWatcher ====================

    def _index_in_watcher(self, chunks: List[str], source: str):
        """Also add learned content to the main knowledge watcher index."""
        try:
            from ai.knowledge_watcher import get_knowledge_watcher
            watcher = get_knowledge_watcher()
            if hasattr(watcher, "indexer") and watcher.indexer:
                pages = [{"page": i + 1, "text": chunk} for i, chunk in enumerate(chunks)]
                watcher.indexer.add_document(source, pages, hashlib.md5(source.encode()).hexdigest())
                logger.debug(f"Indexed {len(chunks)} chunks into knowledge watcher from {source[:50]}")
        except Exception as e:
            logger.debug(f"Could not index in watcher: {e}")

    # ==================== Text Chunking ====================

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text] if text.strip() else []
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                for sep in [". ", ".\n", "\n\n", "\n", " "]:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap
        return chunks


# Singleton
_learner = None


def get_knowledge_learner() -> MonicaKnowledgeLearner:
    global _learner
    if _learner is None:
        _learner = MonicaKnowledgeLearner()
    return _learner
