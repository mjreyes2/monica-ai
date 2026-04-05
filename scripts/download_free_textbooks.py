"""
Download Free Textbook PDFs for Monica's Knowledge Base.

Sources:
  - OpenStax (Rice University) - Free, peer-reviewed college textbooks
  - Open Textbook Library
  - Project Gutenberg (classic science texts)

All books are legally free and openly licensed (CC-BY or similar).
Downloads go to: data/Monica_Knowledge_Base/Textbooks/<Subject>/

Usage:
    python scripts/download_free_textbooks.py
    python scripts/download_free_textbooks.py --subject mathematics
    python scripts/download_free_textbooks.py --list
"""

import os
import sys
import time
import argparse
import hashlib
from pathlib import Path
from urllib.parse import urlparse

# Project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
KB_DIR = PROJECT_ROOT / "data" / "Monica_Knowledge_Base" / "Textbooks"

# ============================================================
# FREE TEXTBOOK CATALOG
# All URLs are direct PDF download links from open-licensed sources
# ============================================================

TEXTBOOK_CATALOG = {
    # ========== MATHEMATICS ==========
    "Mathematics": [
        {
            "title": "College Algebra 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/College-Algebra-2e-WEB.pdf",
            "description": "Functions, polynomials, exponentials, logarithms, systems of equations, sequences, probability",
        },
        {
            "title": "Precalculus 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Precalculus_2e-WEB.pdf",
            "description": "Trigonometry, analytic geometry, conic sections, vectors, parametric equations, polar coordinates",
        },
        {
            "title": "Calculus Volume 1",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Calculus_Volume_1_-_WEB_l4sAIKd.pdf",
            "description": "Limits, derivatives, integrals, fundamental theorem of calculus, applications",
        },
        {
            "title": "Calculus Volume 2",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Calculus_Volume_2_-_WEB.pdf",
            "description": "Integration techniques, differential equations, sequences and series, parametric equations",
        },
        {
            "title": "Calculus Volume 3",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Calculus_Volume_3_-_WEB.pdf",
            "description": "Multivariable calculus, vector calculus, multiple integrals, vector fields, Stokes theorem",
        },
    ],

    # ========== STATISTICS & RESEARCH METHODS ==========
    "Statistics": [
        {
            "title": "Introductory Statistics 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Introductory_Statistics_2e_-_WEB.pdf",
            "description": "Descriptive statistics, probability, distributions, hypothesis testing, regression, chi-square, ANOVA",
        },
        {
            "title": "Introductory Business Statistics 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Introductory_Business_Statistics_2e_-_WEB.pdf",
            "description": "Business applications of statistics, sampling, confidence intervals, linear regression",
        },
    ],

    # ========== CHEMISTRY ==========
    "Chemistry": [
        {
            "title": "Chemistry 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Chemistry2e-WEB.pdf",
            "description": "Atomic structure, bonding, stoichiometry, thermodynamics, kinetics, equilibrium, electrochemistry, organic chemistry",
        },
        {
            "title": "Chemistry - Atoms First 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/ChemistryAtomsFirst2e-WEB.pdf",
            "description": "Atoms-first approach to general chemistry, electronic structure, molecular geometry, reactions",
        },
    ],

    # ========== BIOLOGY ==========
    "Biology": [
        {
            "title": "Biology 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Biology2e-WEB.pdf",
            "description": "Cell biology, genetics, evolution, ecology, plant biology, animal physiology, biodiversity",
        },
        {
            "title": "Concepts of Biology",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/ConceptsofBiology-WEB.pdf",
            "description": "Introduction to biology for non-majors, cell structure, genetics, evolution, ecosystems",
        },
        {
            "title": "Microbiology",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Microbiology-WEB.pdf",
            "description": "Microbial cell biology, metabolism, genetics, virology, immunology, infectious diseases, applied microbiology",
        },
    ],

    # ========== HUMAN ANATOMY & PHYSIOLOGY ==========
    "Anatomy_Physiology": [
        {
            "title": "Anatomy and Physiology 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Anatomy_and_Physiology_2e_-_WEB_c9nD9QL.pdf",
            "description": "All body systems: skeletal, muscular, nervous, endocrine, cardiovascular, respiratory, digestive, urinary, reproductive",
        },
    ],

    # ========== PSYCHOLOGY ==========
    "Psychology": [
        {
            "title": "Psychology 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Psychology2e_WEB.pdf",
            "description": "Biological psychology, sensation, perception, consciousness, learning, memory, cognition, development, personality, disorders, therapy, social psychology",
        },
    ],

    # ========== PHYSICS ==========
    "Physics": [
        {
            "title": "College Physics 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/College_Physics_2e-WEB_7Zesafu.pdf",
            "description": "Mechanics, thermodynamics, waves, optics, electromagnetism, modern physics, nuclear physics",
        },
        {
            "title": "University Physics Volume 1",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/University_Physics_Volume_1_-_WEB.pdf",
            "description": "Mechanics, waves, acoustics - calculus-based physics",
        },
        {
            "title": "University Physics Volume 2",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/University_Physics_Volume_2_-_WEB.pdf",
            "description": "Thermodynamics, electricity, magnetism, optics - calculus-based",
        },
        {
            "title": "University Physics Volume 3",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/UniversityPhysicsVolume3-WEB.pdf",
            "description": "Relativity, quantum mechanics, atomic physics, nuclear physics, particle physics",
        },
    ],

    # ========== COMPUTER SCIENCE ==========
    "Computer_Science": [
        {
            "title": "Introduction to Computer Science",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Introduction_To_Computer_Science_-_WEB.pdf",
            "description": "Algorithms, data structures, programming concepts, networking, databases, security, AI, software engineering",
        },
    ],

    # ========== ENGINEERING ==========
    "Engineering": [
        {
            "title": "Introduction to Engineering Analysis",
            "source": "Open Textbook Library / Kirk Weller",
            "url": "https://open.umn.edu/opentextbooks/formats/1059",
            "description": "Engineering problem solving, units, vectors, forces, equilibrium, circuits",
            "skip_auto": True,  # Requires manual download from open textbook library
        },
    ],

    # ========== GEOGRAPHY & EARTH SCIENCE ==========
    "Geography": [
        {
            "title": "Astronomy 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Astronomy2e-WEB.pdf",
            "description": "Solar system, stars, galaxies, cosmology, space exploration, astrobiology",
        },
    ],

    # ========== GEOMETRY (via Precalculus + supplementary) ==========
    "Geometry": [
        {
            "title": "Elementary Algebra 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/ElementaryAlgebra2e-WEB_3zxfu3Z.pdf",
            "description": "Foundations including geometric concepts, area, volume, Pythagorean theorem, coordinate geometry",
        },
        {
            "title": "Intermediate Algebra 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/IntermediateAlgebra2e-WEB_RlpFLLx.pdf",
            "description": "Conics, radical equations, quadratics, systems - bridges to geometry and precalculus",
        },
        {
            "title": "Algebra and Trigonometry 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Algebra-and-Trigonometry-2e-WEB.pdf",
            "description": "Comprehensive algebra and trigonometry with geometric applications",
        },
    ],

    # ========== ELECTRICAL ENGINEERING ==========
    "Electrical_Engineering": [
        {
            "title": "University Physics Volume 2 (E&M)",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/University_Physics_Volume_2_-_WEB.pdf",
            "description": "Electric charges, fields, Gauss law, capacitance, current, circuits, magnetism, inductance, AC circuits, EM waves",
        },
    ],

    # ========== HUMAN SEXUALITY ==========
    "Human_Sexuality": [
        # No OpenStax book for this, but there are OER resources
        # The Psychology 2e book covers biological bases of behavior and motivation
    ],

    # ========== RESEARCH METHODS ==========
    "Research_Methods": [
        {
            "title": "Psychology 2e (Research Methods chapters)",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Psychology2e_WEB.pdf",
            "description": "Scientific method, research ethics, measurement, experimental design, surveys, qualitative methods, statistics in research",
        },
    ],

    # ========== AERONAUTICS & SPACE ==========
    "Aeronautics": [
        {
            "title": "Astronomy 2e",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Astronomy2e-WEB.pdf",
            "description": "Comprehensive astronomy including orbital mechanics, space exploration, planetary science",
        },
    ],

    # ========== THE BRAIN & NERVOUS SYSTEM (covered by Anatomy + Psychology) ==========
    # These subjects are comprehensively covered in the Anatomy and Physiology 2e
    # and Psychology 2e textbooks (chapters on the nervous system, brain, neurons)

    # ========== DRAMA / THEATER ARTS ==========
    # No OpenStax book; will be covered by built-in knowledge module

    # ========== PUBLIC SPEAKING (Toastmasters-style) ==========
    "Public_Speaking": [
        {
            "title": "Statistics (communication/presentation chapters)",
            "source": "OpenStax",
            "url": "https://assets.openstax.org/oscms-prodcms/media/documents/Statistics-WEB.pdf",
            "description": "Data presentation and communication skills - presenting statistical findings clearly",
        },
    ],
}


def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file with progress display."""
    try:
        import requests
        
        print(f"    Downloading: {url[:80]}...")
        resp = requests.get(url, stream=True, timeout=60, 
                          headers={"User-Agent": "Mozilla/5.0 MonicaAI/1.0 (Educational)"})
        resp.raise_for_status()
        
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = (downloaded / total) * 100
                    mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    print(f"\r    {mb:.1f}/{total_mb:.1f} MB ({pct:.0f}%)", end="", flush=True)
        
        print(f"\r    Downloaded: {dest_path.name} ({downloaded / (1024*1024):.1f} MB)")
        return True
        
    except Exception as e:
        print(f"    ERROR: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return False


def list_catalog():
    """List all available textbooks."""
    print("\n=== AVAILABLE FREE TEXTBOOKS ===\n")
    total = 0
    for subject, books in TEXTBOOK_CATALOG.items():
        if not books:
            continue
        print(f"\n{subject}:")
        for book in books:
            skip = book.get("skip_auto", False)
            marker = " [manual download]" if skip else ""
            print(f"  - {book['title']} ({book['source']}){marker}")
            print(f"    {book['description']}")
            total += 1
    print(f"\nTotal: {total} textbooks across {len(TEXTBOOK_CATALOG)} subjects")


def download_subject(subject: str, books: list, force: bool = False):
    """Download all books for a subject."""
    if not books:
        return 0, 0
    
    subject_dir = KB_DIR / subject
    subject_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded = 0
    skipped = 0
    
    for book in books:
        if book.get("skip_auto"):
            print(f"  [SKIP] {book['title']} - requires manual download from: {book['url']}")
            skipped += 1
            continue
        
        # Generate filename from title
        safe_name = book["title"].replace(" ", "_").replace("/", "-").replace(":", "")
        filename = f"{safe_name}.pdf"
        dest = subject_dir / filename
        
        if dest.exists() and not force:
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"  [EXISTS] {book['title']} ({size_mb:.1f} MB)")
            skipped += 1
            continue
        
        print(f"  [{subject}] {book['title']}")
        if download_file(book["url"], dest):
            downloaded += 1
            # Write metadata
            meta_path = dest.with_suffix(".json")
            import json
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({
                    "title": book["title"],
                    "source": book["source"],
                    "url": book["url"],
                    "description": book["description"],
                    "subject": subject,
                    "downloaded": time.strftime("%Y-%m-%d %H:%M:%S"),
                }, f, indent=2)
        else:
            print(f"  [FAILED] {book['title']}")
        
        time.sleep(1)  # Be polite to servers
    
    return downloaded, skipped


def main():
    parser = argparse.ArgumentParser(description="Download free textbooks for Monica's knowledge base")
    parser.add_argument("--subject", type=str, help="Download only a specific subject")
    parser.add_argument("--list", action="store_true", help="List available textbooks")
    parser.add_argument("--force", action="store_true", help="Re-download existing files")
    args = parser.parse_args()
    
    if args.list:
        list_catalog()
        return
    
    print("=" * 60)
    print("MONICA AI - Free Textbook Downloader")
    print(f"Destination: {KB_DIR}")
    print("=" * 60)
    
    total_downloaded = 0
    total_skipped = 0
    
    subjects = TEXTBOOK_CATALOG.keys()
    if args.subject:
        # Find matching subject (case-insensitive)
        match = None
        for s in subjects:
            if s.lower() == args.subject.lower():
                match = s
                break
        if not match:
            print(f"Subject not found: {args.subject}")
            print(f"Available: {', '.join(subjects)}")
            return
        subjects = [match]
    
    for subject in subjects:
        books = TEXTBOOK_CATALOG[subject]
        if not books:
            continue
        print(f"\n--- {subject} ({len(books)} books) ---")
        d, s = download_subject(subject, books, args.force)
        total_downloaded += d
        total_skipped += s
    
    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {total_downloaded} downloaded, {total_skipped} skipped")
    print(f"Knowledge base: {KB_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
