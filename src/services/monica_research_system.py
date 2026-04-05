"""
Monica AI - Research System

Provides scholarly research, academic search, and multi-language support
for the hologram system and AI service.

Features:
- Academic paper search via free APIs (Semantic Scholar, CrossRef, arXiv)
- Wikipedia summaries in multiple languages
- Dictionary/thesaurus lookups
- Multi-language translation context
- Research overlay for hologram display

Usage:
    from services.monica_research_system import get_research_window, get_language_support
    rw = get_research_window()
    results = rw.search_papers("quantum computing")
"""

import json
import logging
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger("Monica.Research")

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


@dataclass
class Paper:
    """A research paper result."""
    title: str
    authors: List[str]
    year: int = 0
    abstract: str = ""
    url: str = ""
    citations: int = 0
    source: str = ""


@dataclass
class LanguageInfo:
    """Language support info."""
    code: str
    name: str
    native_name: str
    greeting: str


class ResearchWindow:
    """
    Research overlay window for the hologram system.
    Provides academic search and displays results.
    """

    def __init__(self):
        self.visible = False
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self.last_results: List[Paper] = []
        self.current_query: str = ""
        logger.info("Research Window created")

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def _fetch_json(self, url: str, timeout: int = 10) -> Optional[Dict]:
        cache_key = url
        if cache_key in self._cache and time.time() - self._cache_ttl.get(cache_key, 0) < 300:
            return self._cache[cache_key]
        try:
            headers = {"User-Agent": "MonicaAI/1.0 (Educational Research Assistant)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._cache[cache_key] = data
                self._cache_ttl[cache_key] = time.time()
                return data
        except Exception as e:
            logger.debug(f"Research API error: {e}")
            return None

    def search_papers(self, query: str, limit: int = 10) -> List[Paper]:
        """Search academic papers via Semantic Scholar (free, no API key)."""
        self.current_query = query
        encoded = urllib.parse.quote(query)
        url = (f"https://api.semanticscholar.org/graph/v1/paper/search?"
               f"query={encoded}&limit={limit}&fields=title,authors,year,abstract,url,citationCount")

        data = self._fetch_json(url)
        if not data:
            return []

        papers = []
        for item in data.get("data", []):
            authors = [a.get("name", "") for a in item.get("authors", [])]
            papers.append(Paper(
                title=item.get("title", ""),
                authors=authors[:3],
                year=item.get("year", 0) or 0,
                abstract=(item.get("abstract") or "")[:300],
                url=item.get("url", ""),
                citations=item.get("citationCount", 0) or 0,
                source="Semantic Scholar",
            ))

        self.last_results = papers
        return papers

    def search_arxiv(self, query: str, limit: int = 5) -> List[Paper]:
        """Search arXiv preprints (free, no API key)."""
        encoded = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{encoded}&max_results={limit}"

        try:
            headers = {"User-Agent": "MonicaAI/1.0"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8")

            papers = []
            # Simple XML parsing without external deps
            entries = content.split("<entry>")[1:]
            for entry in entries:
                title = self._extract_xml(entry, "title").strip().replace("\n", " ")
                abstract = self._extract_xml(entry, "summary").strip()[:300]
                link = ""
                if 'href="http' in entry:
                    start = entry.index('href="http') + 6
                    end = entry.index('"', start)
                    link = entry[start:end]
                papers.append(Paper(
                    title=title,
                    authors=[],
                    abstract=abstract,
                    url=link,
                    source="arXiv",
                ))
            self.last_results.extend(papers)
            return papers
        except Exception as e:
            logger.debug(f"arXiv search error: {e}")
            return []

    def _extract_xml(self, text: str, tag: str) -> str:
        try:
            start = text.index(f"<{tag}>") + len(tag) + 2
            end = text.index(f"</{tag}>")
            return text[start:end]
        except ValueError:
            return ""

    def search_wikipedia(self, query: str, lang: str = "en") -> Optional[str]:
        """Get Wikipedia summary (free, no API key)."""
        encoded = urllib.parse.quote(query)
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        data = self._fetch_json(url)
        if data and "extract" in data:
            return data["extract"]
        return None

    def define_word(self, word: str) -> Optional[Dict]:
        """Get dictionary definition (free API)."""
        encoded = urllib.parse.quote(word.lower())
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{encoded}"
        data = self._fetch_json(url)
        if data and isinstance(data, list) and data:
            entry = data[0]
            meanings = []
            for m in entry.get("meanings", []):
                for d in m.get("definitions", [])[:2]:
                    meanings.append({
                        "part_of_speech": m.get("partOfSpeech", ""),
                        "definition": d.get("definition", ""),
                        "example": d.get("example", ""),
                    })
            return {
                "word": entry.get("word", word),
                "phonetic": entry.get("phonetic", ""),
                "meanings": meanings,
            }
        return None

    def render(self, frame) -> Any:
        """Render research results overlay on a frame."""
        if not self.visible or not HAS_CV2 or not self.last_results:
            return frame

        h, w = frame.shape[:2]
        panel_w = 350
        panel_h = min(h - 40, 50 + len(self.last_results) * 60)
        px = 20
        py = 20

        overlay = frame.copy()
        cv2.rectangle(overlay, (px, py), (px + panel_w, py + panel_h), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        cv2.rectangle(frame, (px, py), (px + panel_w, py + panel_h), (0, 200, 255), 1)

        cv2.putText(frame, f"RESEARCH: {self.current_query[:30]}", (px + 10, py + 20),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        y = py + 45
        for paper in self.last_results[:6]:
            title = paper.title[:45] + "..." if len(paper.title) > 45 else paper.title
            cv2.putText(frame, title, (px + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)
            info = f"{paper.year} | {paper.citations} cites | {paper.source}"
            cv2.putText(frame, info, (px + 10, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (150, 150, 150), 1)
            y += 55

        return frame

    def get_status(self) -> Dict[str, Any]:
        return {
            "visible": self.visible,
            "last_query": self.current_query,
            "results_count": len(self.last_results),
            "cache_entries": len(self._cache),
        }


class LanguageSupport:
    """Multi-language support for research and translation context."""

    LANGUAGES = {
        "en": LanguageInfo("en", "English", "English", "Hello"),
        "es": LanguageInfo("es", "Spanish", "Espanol", "Hola"),
        "fr": LanguageInfo("fr", "French", "Francais", "Bonjour"),
        "de": LanguageInfo("de", "German", "Deutsch", "Hallo"),
        "it": LanguageInfo("it", "Italian", "Italiano", "Ciao"),
        "pt": LanguageInfo("pt", "Portuguese", "Portugues", "Ola"),
        "ru": LanguageInfo("ru", "Russian", "Russkiy", "Privet"),
        "zh": LanguageInfo("zh", "Chinese", "Zhongwen", "Ni hao"),
        "ja": LanguageInfo("ja", "Japanese", "Nihongo", "Konnichiwa"),
        "ko": LanguageInfo("ko", "Korean", "Hangugeo", "Annyeong"),
        "ar": LanguageInfo("ar", "Arabic", "Al-Arabiyya", "Marhaba"),
        "hi": LanguageInfo("hi", "Hindi", "Hindi", "Namaste"),
        "ht": LanguageInfo("ht", "Haitian Creole", "Kreyol Ayisyen", "Bonjou"),
    }

    def __init__(self):
        self.current_language = "en"
        logger.info(f"Language Support initialized ({len(self.LANGUAGES)} languages)")

    def get_language(self, code: str) -> Optional[LanguageInfo]:
        return self.LANGUAGES.get(code)

    def list_languages(self) -> List[LanguageInfo]:
        return list(self.LANGUAGES.values())

    def set_language(self, code: str) -> bool:
        if code in self.LANGUAGES:
            self.current_language = code
            return True
        return False

    def get_wikipedia_summary(self, query: str, lang: str = None) -> Optional[str]:
        lang = lang or self.current_language
        encoded = urllib.parse.quote(query)
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        try:
            headers = {"User-Agent": "MonicaAI/1.0"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("extract")
        except Exception:
            return None


# Singletons
_research_window: Optional[ResearchWindow] = None
_language_support: Optional[LanguageSupport] = None


def get_research_window() -> ResearchWindow:
    global _research_window
    if _research_window is None:
        _research_window = ResearchWindow()
    return _research_window


def get_language_support() -> LanguageSupport:
    global _language_support
    if _language_support is None:
        _language_support = LanguageSupport()
    return _language_support
