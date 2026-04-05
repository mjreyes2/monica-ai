"""Test PDF knowledge extraction and retrieval end-to-end."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai.knowledge_watcher import KnowledgeWatcher, PDFTextExtractor, TextExtractor
from pathlib import Path

print("=" * 60)
print("  PDF KNOWLEDGE RETRIEVAL TEST")
print("=" * 60)

passed = 0
failed = 0

def check(label, cond):
    global passed, failed
    if cond:
        print(f"  [OK] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}")
        failed += 1

# 1. PDF extraction
print("\n--- PDF Extraction ---")
pdf_ext = PDFTextExtractor()
check("PDF extractor created", pdf_ext is not None)
check("PyMuPDF backend available", getattr(pdf_ext, '_backend', None) == "pymupdf")

pdf_dir = Path(__file__).parent.parent / "data" / "Monica_Knowledge_Base" / "Textbooks"
pdfs = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
check(f"Found PDFs in KB ({len(pdfs)})", len(pdfs) > 0)

if pdfs:
    test_pdf = pdfs[0]
    text = pdf_ext.extract(test_pdf)
    check(f"Extracted text from {test_pdf.name[:40]}... ({len(text)} chars)", len(text) > 100)

# 2. Text extractor (all file types)
print("\n--- Text Extractor ---")
ext = TextExtractor()
check("TextExtractor has extract()", hasattr(ext, "extract") or hasattr(ext, "extract_text"))

# 3. Knowledge Watcher indexing
print("\n--- Knowledge Watcher Indexing ---")
kw = KnowledgeWatcher()
check("KnowledgeWatcher created", kw is not None)
check("Has indexer", kw.indexer is not None)
check("Has extractor", kw.extractor is not None)

# Index one PDF
if pdfs:
    import hashlib
    fhash = hashlib.md5(str(pdfs[0]).encode()).hexdigest()
    kw._process_file(pdfs[0], fhash)
    stats = kw.get_stats()
    check(f"Indexed PDF -> {stats.get('total_documents', 0)} docs", stats.get("total_documents", 0) > 0)
    check(f"Created {stats.get('total_chunks', 0)} chunks", stats.get("total_chunks", 0) > 0)

# 4. Search and retrieval
print("\n--- Search & Retrieval ---")
# Search for terms that exist in the indexed PDF (math book)
results = kw.search("math algebra practice problems")
print(f"  Chunks in indexer: {len(kw.indexer.chunks)}")
check(f"Search returned {len(results)} results", len(results) > 0)
if results:
    r = results[0]
    check("Result has 'text' field", "text" in r)
    check("Result has 'source' field", "source" in r)
    check("Result has 'score' field", "score" in r)
    check(f"Result text length: {len(r.get('text', ''))}", len(r.get("text", "")) > 20)

# 5. get_context for AI prompt
ctx = kw.get_context("math algebra")
check(f"get_context returns text ({len(ctx)} chars)", len(ctx) > 0)

print(f"\n{'=' * 60}")
print(f"Results: {passed} passed, {failed} failed out of {passed + failed} checks")
print(f"{'=' * 60}")
if failed == 0:
    print("ALL CHECKS PASSED!")
