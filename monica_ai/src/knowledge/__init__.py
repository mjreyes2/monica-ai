"""
Knowledge Base System for Monica AI.

Provides:
- PDF indexing and search
- Scientific document knowledge
- Human body/medical information retrieval
"""

from .pdf_knowledge_base import (
    PDFKnowledgeBase,
    PDFDocument,
    PDFPage,
    SearchResult,
)

__all__ = [
    'PDFKnowledgeBase',
    'PDFDocument',
    'PDFPage',
    'SearchResult',
]
