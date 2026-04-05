"""
Download a pre-trained KenLM language model
"""

import os
import sys
import requests
from tqdm import tqdm

def download_file(url, output_path):
    """
    Download a file with progress bar.
    """
    print(f" Downloading: {url}")
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as f, tqdm(
        total=total_size,
        unit='B',
        unit_scale=True,
        desc=output_path
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
    
    print(f"[OK] Downloaded: {output_path}")
    return output_path

def download_librispeech_lm():
    """
    Download pre-trained LibriSpeech language model.
    """
    print("\n" + "="*80)
    print("DOWNLOADING PRE-TRAINED LANGUAGE MODEL")
    print("="*80 + "\n")
    
    # LibriSpeech 4-gram model from Kaldi
    url = "http://www.openslr.org/resources/11/4-gram.arpa.gz"
    output_gz = "4-gram.arpa.gz"
    output_arpa = "librispeech_4gram.arpa"
    
    try:
        # Download
        if not os.path.exists(output_gz):
            download_file(url, output_gz)
        else:
            print(f"[OK] Already downloaded: {output_gz}")
        
        # Decompress
        print(f"\n[PKG] Decompressing...")
        import gzip
        import shutil
        
        with gzip.open(output_gz, 'rb') as f_in:
            with open(output_arpa, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print(f"[OK] Decompressed: {output_arpa}")
        
        # Convert to binary for faster loading
        print(f"\n Converting to binary format...")
        
        # Add KenLM to path dynamically
        kenlm_dir = os.path.join(os.path.dirname(__file__), 'kenlm', 'python')
        if os.path.exists(kenlm_dir) and kenlm_dir not in sys.path:
            sys.path.insert(0, kenlm_dir)
        build_binary = os.path.join(kenlm_dir, "build", "bin", "build_binary.exe")
        
        if os.path.exists(build_binary):
            import subprocess
            output_bin = "librispeech_4gram.bin"
            
            result = subprocess.run(
                [build_binary, output_arpa, output_bin],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[OK] Binary model created: {output_bin}")
                
                # Test the model
                print(f"\n[TEST] Testing model...")
                import kenlm
                model = kenlm.Model(output_bin)
                
                test_sentence = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"
                score = model.score(test_sentence, bos=True, eos=True)
                
                print(f"[OK] Model loaded successfully!")
                print(f"   Order: {model.order}")
                print(f"   Test score: {score:.2f}")
                
                print("\n" + "="*80)
                print("[OK] SUCCESS! Pre-trained model ready to use")
                print("="*80)
                print(f"\nModel path: {os.path.abspath(output_bin)}")
                print("\nTo use in your code:")
                print(f"   pipeline = EnhancedSTTPipeline(")
                print(f"       kenlm_model_path=r'{os.path.abspath(output_bin)}'")
                print(f"   )")
                
                return output_bin
            else:
                print(f"[WARN]  Binary conversion failed, using ARPA format")
                return output_arpa
        else:
            print(f"[WARN]  build_binary not found, using ARPA format")
            return output_arpa
            
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_simple_lm():
    """
    Create a very simple language model for testing.
    """
    print("\n[NOTE] Creating simple test language model...")
    
    # Create minimal training data
    text = """
THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG
SPEECH RECOGNITION WORKS WELL WITH LANGUAGE MODELS
NATURAL LANGUAGE PROCESSING IS VERY USEFUL
MACHINE LEARNING IMPROVES TRANSCRIPTION ACCURACY
ARTIFICIAL INTELLIGENCE HELPS WITH SPEECH TO TEXT
"""
    
    with open("simple_text.txt", "w") as f:
        f.write(text * 10)  # Repeat to have more data
    
    print("[OK] Created simple_text.txt")
    
    # Build simple 3-gram model
    kenlm_dir = os.path.join(os.path.dirname(__file__), 'kenlm')
    if os.path.exists(kenlm_dir) and kenlm_dir not in sys.path:
        sys.path.insert(0, kenlm_dir)
    lmplz = os.path.join(kenlm_dir, "build", "bin", "lmplz.exe")
    
    if not os.path.exists(lmplz):
        print(f"[X] lmplz not found at: {lmplz}")
        return None
    
    output_arpa = "simple_3gram.arpa"
    
    print(" Training 3-gram model...")
    
    try:
        import subprocess
        
        # Use smaller memory settings
        with open("simple_text.txt", "r") as infile:
            with open(output_arpa, "w") as outfile:
                result = subprocess.run(
                    [lmplz, "-o", "3", "--discount_fallback"],
                    stdin=infile,
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"Error: {result.stderr}")
                    return None
        
        print(f"[OK] Created: {output_arpa}")
        
        # Test it
        import kenlm
        model = kenlm.Model(output_arpa)
        print(f"[OK] Model works! Order: {model.order}")
        
        return output_arpa
        
    except Exception as e:
        print(f"[X] Error: {e}")
        return None

if __name__ == "__main__":
    print("\nChoose language model source:")
    print("1. Download pre-trained LibriSpeech 4-gram (~800MB, recommended)")
    print("2. Create simple test model (quick, limited accuracy)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        model_path = download_librispeech_lm()
    else:
        model_path = create_simple_lm()
    
    if model_path:
        print(f"\n[OK] Language model ready: {model_path}")
    else:
        print("\n[X] Failed to create language model")
