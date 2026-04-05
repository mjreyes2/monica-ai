"""
PDF Knowledge Base Indexer (lightweight)

- Recursively scans a folder for PDFs
- Extracts text (PyPDF2) with robust fallbacks
- Splits into overlapping chunks
- Creates embeddings with sentence-transformers if available; otherwise stores plain text chunks only
- Saves an index (embeddings + metadata) under models/kb_index/<name>
  - embeddings.npy  (float32 matrix) if embeddings available
  - meta.jsonl      (one JSON per chunk: source, page, offset, text)

Usage:
  python -m monica_ai.knowledge.pdf_indexer --root "D:\\Books PDF" --name books_pdf

Retrieval (example):
  from monica_ai.knowledge.pdf_indexer import PDFIndex
  idx = PDFIndex.load("models/kb_index/books_pdf")
  results = idx.search("quantum entanglement limits", top_k=5)
  for r in results: print(r['score'], r['source'], r['text'][:120])
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Optional dependencies
try:
    import PyPDF2
    HAS_PYPDF2 = True
except Exception:
    HAS_PYPDF2 = False

try:
    from sentence_transformers import SentenceTransformer
    from numpy.linalg import norm
    HAS_ST = True
except Exception:
    HAS_ST = False


def _read_pdf_text(path: Path) -> List[Tuple[int, str]]:
    """Return list of (page_index, text) tuples."""
    pages: List[Tuple[int, str]] = []
    if HAS_PYPDF2:
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text() or ""
                    except Exception:
                        text = ""
                    pages.append((i, text))
            return pages
        except Exception:
            return [(0, "")]  # minimal fallback
    else:
        return [(0, "")]  # PyPDF2 not installed


def _chunk_text(text: str, chunk_chars: int = 1200, overlap: int = 200) -> List[str]:
    text = text.replace("\r", " ").replace("\n", " ")
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_chars)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
        if start >= len(text):
            break
    return chunks


def _embed_texts(texts: List[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Optional[np.ndarray]:
    if not HAS_ST:
        return None
    try:
        model = SentenceTransformer(model_name)
        embs = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
        embs = np.asarray(embs, dtype=np.float32)
        return embs
    except Exception:
        return None


@dataclass
class IndexPaths:
    root: Path
    meta_path: Path
    emb_path: Path

    @staticmethod
    def from_dir(out_dir: Path) -> "IndexPaths":
        out_dir.mkdir(parents=True, exist_ok=True)
        return IndexPaths(
            root=out_dir,
            meta_path=out_dir / "meta.jsonl",
            emb_path=out_dir / "embeddings.npy",
        )


class PDFIndex:
    def __init__(self, meta: List[Dict[str, Any]], embeddings: Optional[np.ndarray]):
        self.meta = meta
        self.embeddings = embeddings

    @staticmethod
    def load(dir_path: str | Path) -> "PDFIndex":
        p = IndexPaths.from_dir(Path(dir_path))
        meta: List[Dict[str, Any]] = []
        if p.meta_path.exists():
            with open(p.meta_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        meta.append(json.loads(line))
        embs = None
        if p.emb_path.exists():
            embs = np.load(p.emb_path)
        return PDFIndex(meta, embs)

    def save(self, dir_path: str | Path):
        p = IndexPaths.from_dir(Path(dir_path))
        with open(p.meta_path, "w", encoding="utf-8") as f:
            for m in self.meta:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        if self.embeddings is not None:
            np.save(p.emb_path, self.embeddings)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.embeddings is None or not HAS_ST:
            # Fallback: naive substring ranking
            scored = []
            q = query.lower()
            for i, m in enumerate(self.meta):
                text = m.get("text", "").lower()
                score = 1.0 if q in text else 0.0
                if score > 0:
                    scored.append((score, i))
            scored.sort(reverse=True)
            return [dict(self.meta[i], score=float(s)) for s, i in scored[:top_k]]

        # Embedding search
        q_emb = _embed_texts([query])
        if q_emb is None:
            return []
        qv = q_emb[0]
        sims = np.dot(self.embeddings, qv)
        # embeddings are normalized, dot = cosine similarity
        idxs = np.argsort(-sims)[:top_k]
        return [dict(self.meta[i], score=float(sims[i])) for i in idxs]


def build_index(root: str, name: str = "books_pdf", out_dir: Optional[str] = None,
                chunk_chars: int = 1200, overlap: int = 200) -> PDFIndex:
    root_path = Path(root)
    out_base = Path(out_dir) if out_dir else Path("models/kb_index") / name
    paths = IndexPaths.from_dir(out_base)

    all_chunks: List[str] = []
    meta: List[Dict[str, Any]] = []

    pdfs: List[Path] = []
    for p in root_path.rglob("*.pdf"):
        pdfs.append(p)

    print(f"[KB] Found {len(pdfs)} PDF files under: {root_path}")

    for pdf_path in pdfs:
        try:
            pages = _read_pdf_text(pdf_path)
            for page_idx, text in pages:
                if not text:
                    continue
                chunks = _chunk_text(text, chunk_chars=chunk_chars, overlap=overlap)
                for offset, ch in enumerate(chunks):
                    meta.append({
                        "source": str(pdf_path),
                        "page": int(page_idx) + 1,
                        "offset": int(offset),
                        "text": ch,
                    })
                    all_chunks.append(ch)
        except Exception as e:
            print(f"[KB] Skipping {pdf_path}: {e}")

    print(f"[KB] Total chunks: {len(all_chunks)}")
    embeddings = _embed_texts(all_chunks) if all_chunks else None
    if embeddings is None:
        print("[KB] Embeddings unavailable (missing sentence-transformers). Indexing text only.")

    index = PDFIndex(meta=meta, embeddings=embeddings)
    index.save(paths.root)
    print(f"[KB] Index saved to: {paths.root}")
    if embeddings is not None:
        print(f"[KB] Embeddings shape: {embeddings.shape}")
    return index


def main():
    ap = argparse.ArgumentParser(description="Index PDFs for Monica's knowledge base")
    ap.add_argument("--root", required=True, help="Root folder with PDFs (recursive)")
    ap.add_argument("--name", default="books_pdf", help="Index name (subfolder under models/kb_index)")
    ap.add_argument("--out", default=None, help="Optional explicit output directory")
    ap.add_argument("--chunk", type=int, default=1200, help="Chunk size in characters")
    ap.add_argument("--overlap", type=int, default=200, help="Overlap in characters")
    args = ap.parse_args()

    if not HAS_PYPDF2:
        print("PyPDF2 is not installed. Run: pip install PyPDF2")
    if not HAS_ST:
        print("sentence-transformers not installed. Run: pip install sentence-transformers")

    build_index(args.root, name=args.name, out_dir=args.out, chunk_chars=args.chunk, overlap=args.overlap)


if __name__ == "__main__":
    main()
