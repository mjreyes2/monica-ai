#!/usr/bin/env python3
"""Extract paragraphs from PDF for STT training"""
import subprocess
import sys

# Install PyPDF2 if needed
subprocess.run([sys.executable, "-m", "pip", "install", "PyPDF2", "-q"], check=False)

from PyPDF2 import PdfReader
from pathlib import Path
import re

PDF_FOLDER = Path(r"D:\Books PDF")
OUTPUT_FILE = Path(__file__).parent / "stt_training_phrases.txt"
TARGET_PHRASES = 33000

def extract_paragraphs(pdf_path):
    """Extract paragraphs from PDF"""
    print(f"Reading PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    
    paragraphs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            # Split into sentences more aggressively
            # First clean up the text
            text = ' '.join(text.split())
            
            # Split by sentence endings
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            for sent in sentences:
                clean = sent.strip()
                # Accept sentences between 10 and 300 characters (good for reading aloud)
                if 10 < len(clean) < 300 and len(clean.split()) >= 3:
                    # Remove special characters that are hard to read
                    clean = re.sub(r'[^\w\s.,;:!?\'"()-]', '', clean)
                    if clean and len(clean) > 10:
                        paragraphs.append(clean)
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(reader.pages)} pages, extracted {len(paragraphs)} so far...")
    
    return paragraphs

def main():
    # Load existing phrases
    existing = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = set(line.strip() for line in f if line.strip())
    
    print(f"Existing phrases: {len(existing)}")
    print(f"Target: {TARGET_PHRASES}")
    
    # Find all PDFs recursively
    pdf_files = list(PDF_FOLDER.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {PDF_FOLDER}")
    
    all_phrases = existing.copy()
    
    for pdf_path in pdf_files:
        if len(all_phrases) >= TARGET_PHRASES:
            print(f"\nReached target of {TARGET_PHRASES} phrases!")
            break
            
        try:
            new_paragraphs = extract_paragraphs(pdf_path)
            before = len(all_phrases)
            all_phrases.update(new_paragraphs)
            added = len(all_phrases) - before
            print(f"  Added {added} new unique sentences (total: {len(all_phrases)})")
        except Exception as e:
            print(f"  Error reading {pdf_path.name}: {e}")
            continue
    
    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for phrase in all_phrases:
            f.write(phrase + '\n')
    
    print(f"\n{'='*50}")
    print(f"Total phrases now: {len(all_phrases)}")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
