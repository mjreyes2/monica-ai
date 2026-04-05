"""
Index PDFs from D: Drive for Monica AI Knowledge Base

This script scans the D: drive (MaxOne Drive) for scientific PDFs
and builds a searchable knowledge base for Monica.

Usage:
    python index_pdfs_d_drive.py
"""

import sys
from pathlib import Path

# Add project root and src/ to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

try:
    from ai.pdf_retriever import PDFKnowledgeBase
except ImportError:
    # Fallback stub if pdf_retriever doesn't export this class
    PDFKnowledgeBase = None
    print('[WARNING] PDFKnowledgeBase not available')

def main():
    print("=" * 70)
    print("MONICA AI - PDF KNOWLEDGE BASE INDEXER")
    print("=" * 70)
    print()
    print("This will scan D: drive for PDF documents and build a searchable")
    print("knowledge base for scientific information (especially human body/medical).")
    print()

    # Check if D: drive exists
    d_drive = Path("D:/")
    if not d_drive.exists():
        print("[ERROR] D: drive not found!")
        print("        Please verify the drive letter and try again.")
        return

    print(f"[OK] D: drive found: {d_drive}")
    print()

    # Create knowledge base
    print("Initializing knowledge base...")
    kb = PDFKnowledgeBase()
    print()

    # Show current statistics
    stats = kb.get_statistics()
    print("Current Index Statistics:")
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Pages: {stats['total_pages']}")
    print(f"  Words: {stats['total_words']:,}")
    print(f"  Unique words: {stats['unique_words']:,}")
    print(f"  Total size: {stats['total_size_mb']:.1f} MB")
    print(f"  Semantic search: {'Available' if stats['semantic_search_available'] else 'Not available'}")
    print()

    # Ask for confirmation
    print("[WARNING] Indexing entire D: drive may take a while!")
    print("          Consider indexing specific directories if you have many PDFs.")
    print()

    response = input("Do you want to index D: drive? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Indexing cancelled.")
        return

    print()
    print("Starting indexing...")
    print("This may take several minutes depending on the number of PDFs.")
    print()

    # Index D: drive
    try:
        new_docs = kb.index_directory(
            directory=d_drive,
            recursive=True,
            extensions=['.pdf']
        )

        print()
        print("=" * 70)
        print("INDEXING COMPLETE!")
        print("=" * 70)
        print()

        # Show updated statistics
        stats = kb.get_statistics()
        print("Updated Index Statistics:")
        print(f"  Documents: {stats['total_documents']} (+{new_docs} new)")
        print(f"  Pages: {stats['total_pages']}")
        print(f"  Words: {stats['total_words']:,}")
        print(f"  Unique words: {stats['unique_words']:,}")
        print(f"  Total size: {stats['total_size_mb']:.1f} MB")
        print()

        print("Knowledge base ready!")
        print("Monica can now search your scientific PDFs for information.")
        print()

        # Test search
        print("Testing search functionality...")
        test_query = "heart anatomy"
        results = kb.search(test_query, max_results=3)

        if results:
            print(f"\nTest search results for '{test_query}':")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. {result.doc_title}")
                print(f"     Page {result.page_number} | Score: {result.score:.2f}")
                print(f"     {result.snippet[:150]}...")
        else:
            print(f"\nNo results found for '{test_query}'")

        print()
        print("[SUCCESS] All done! Knowledge base is ready for Monica.")

    except Exception as e:
        print(f"\n[ERROR] Error during indexing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
