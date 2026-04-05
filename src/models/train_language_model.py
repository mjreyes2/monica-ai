"""
Train a KenLM language model for STT enhancement
"""

import os
import sys

# Add KenLM to path dynamically
kenlm_path = os.path.join(os.path.dirname(__file__), 'kenlm')
if os.path.exists(kenlm_path) and kenlm_path not in sys.path:
    sys.path.insert(0, kenlm_path)

from datasets import load_dataset
import subprocess

def download_training_data(output_file="training_text.txt", num_samples=10000):
    """
    Download training data from LibriSpeech transcripts.
    """
    print("[?] Downloading LibriSpeech training data...")
    
    try:
        # Load LibriSpeech dataset (transcripts only)
        dataset = load_dataset("librispeech_asr", "clean", split="train.100", streaming=True)
        
        print(f"[OK] Dataset loaded, extracting {num_samples} samples...")
        
        # Extract text and save to file
        with open(output_file, "w", encoding="utf-8") as f:
            count = 0
            for sample in dataset:
                text = sample["text"].strip()
                if text:
                    f.write(text + "\n")
                    count += 1
                    if count >= num_samples:
                        break
                    
                    if count % 1000 == 0:
                        print(f"   Processed {count} samples...")
        
        print(f"[OK] Saved {count} text samples to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"[X] Error downloading data: {e}")
        print("   Creating sample data instead...")
        return create_sample_data(output_file)

def create_sample_data(output_file="training_text.txt"):
    """
    Create sample training data for testing.
    """
    sample_texts = [
        "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
        "SPEECH RECOGNITION TECHNOLOGY HAS IMPROVED SIGNIFICANTLY",
        "NATURAL LANGUAGE PROCESSING ENABLES BETTER UNDERSTANDING",
        "MACHINE LEARNING MODELS CAN TRANSCRIBE AUDIO ACCURATELY",
        "LANGUAGE MODELS HELP IMPROVE TRANSCRIPTION QUALITY",
        "ARTIFICIAL INTELLIGENCE IS TRANSFORMING COMMUNICATION",
        "VOICE ASSISTANTS USE SPEECH TO TEXT TECHNOLOGY",
        "DEEP LEARNING NETWORKS PROCESS AUDIO SIGNALS",
        "ACOUSTIC MODELS CONVERT SOUND WAVES TO TEXT",
        "BEAM SEARCH DECODING IMPROVES RECOGNITION ACCURACY"
    ]
    
    with open(output_file, "w", encoding="utf-8") as f:
        # Repeat samples to create more data
        for _ in range(100):
            for text in sample_texts:
                f.write(text + "\n")
    
    print(f"[OK] Created sample training data: {output_file}")
    return output_file

def train_kenlm_model(
    text_file,
    output_arpa="language_model.arpa",
    output_binary="language_model.bin",
    ngram_order=5
):
    """
    Train a KenLM language model.
    """
    print(f"\n[?] Training {ngram_order}-gram KenLM model...")
    
    kenlm_dir = r"C:\Monica\kenlm"
    lmplz_path = os.path.join(kenlm_dir, "build", "bin", "lmplz.exe")
    build_binary_path = os.path.join(kenlm_dir, "build", "bin", "build_binary.exe")
    
    # Check if executables exist
    if not os.path.exists(lmplz_path):
        print(f"[X] lmplz not found at: {lmplz_path}")
        print("   Please ensure KenLM was built successfully.")
        return None
    
    # Step 1: Train ARPA model
    print(f"   Step 1: Training ARPA model (order={ngram_order})...")
    
    try:
        with open(text_file, "r", encoding="utf-8") as infile:
            with open(output_arpa, "w", encoding="utf-8") as outfile:
                result = subprocess.run(
                    [lmplz_path, "-o", str(ngram_order)],
                    stdin=infile,
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"[X] Error training ARPA model:")
                    print(result.stderr)
                    return None
        
        print(f"   [OK] ARPA model saved: {output_arpa}")
        
    except Exception as e:
        print(f"[X] Error running lmplz: {e}")
        return None
    
    # Step 2: Convert to binary format (faster loading)
    print(f"   Step 2: Converting to binary format...")
    
    try:
        result = subprocess.run(
            [build_binary_path, output_arpa, output_binary],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"[X] Error building binary model:")
            print(result.stderr)
            return output_arpa  # Return ARPA if binary fails
        
        print(f"   [OK] Binary model saved: {output_binary}")
        return output_binary
        
    except Exception as e:
        print(f"[WARN]  Warning: Could not create binary model: {e}")
        print(f"   Using ARPA model instead: {output_arpa}")
        return output_arpa

def test_language_model(model_path):
    """
    Test the trained language model.
    """
    print(f"\n[TEST] Testing language model: {model_path}")
    
    try:
        import kenlm
        
        model = kenlm.Model(model_path)
        
        print(f"[OK] Model loaded successfully!")
        print(f"   Order: {model.order}")
        
        # Test sentences
        test_sentences = [
            "THE QUICK BROWN FOX",
            "SPEECH RECOGNITION WORKS WELL",
            "RANDOM GIBBERISH WORDS HERE"
        ]
        
        print("\n[CHART] Test scores (lower = more likely):")
        for sentence in test_sentences:
            score = model.score(sentence, bos=True, eos=True)
            perplexity = model.perplexity(sentence)
            print(f"   '{sentence}'")
            print(f"      Score: {score:.2f}, Perplexity: {perplexity:.2f}")
        
        return True
        
    except Exception as e:
        print(f"[X] Error testing model: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("KENLM LANGUAGE MODEL TRAINING")
    print("="*80 + "\n")
    
    # Step 1: Get training data
    print("Choose training data source:")
    print("1. Download LibriSpeech transcripts (recommended, ~10k samples)")
    print("2. Use sample data (quick test, limited accuracy)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        text_file = download_training_data(num_samples=10000)
    else:
        text_file = create_sample_data()
    
    if not text_file or not os.path.exists(text_file):
        print("[X] Failed to create training data")
        sys.exit(1)
    
    # Step 2: Train model
    model_path = train_kenlm_model(
        text_file,
        output_arpa="english_5gram.arpa",
        output_binary="english_5gram.bin",
        ngram_order=5
    )
    
    if not model_path:
        print("\n[X] Training failed!")
        sys.exit(1)
    
    # Step 3: Test model
    if test_language_model(model_path):
        print("\n" + "="*80)
        print("[OK] SUCCESS! Language model trained and tested")
        print("="*80)
        print(f"\nModel saved to: {os.path.abspath(model_path)}")
        print("\nTo use with enhanced_stt_pipeline.py:")
        print(f"   pipeline = EnhancedSTTPipeline(")
        print(f"       kenlm_model_path=r'{os.path.abspath(model_path)}'")
        print(f"   )")
    else:
        print("\n[WARN]  Model trained but testing failed")
