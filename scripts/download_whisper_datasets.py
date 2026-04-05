#!/usr/bin/env python3
"""
Monica AI — Whisper Fine-Tuning Dataset Downloader
===================================================
Downloads large-scale, diverse speech datasets for fine-tuning OpenAI Whisper.
All datasets are FREE and require NO account (except Common Voice).

Datasets downloaded:
  1. LibriSpeech train-clean-100  (~28,539 samples, US English, read speech)
  2. LibriSpeech train-clean-360  (~104,014 samples, US English, read speech)
  3. VoxPopuli English             (~180,000+ samples, European accents)
  4. [Optional] Common Voice 17 EN (~100,000+ samples, global accents — needs HF token)

Total: 300,000+ diverse speech samples from multiple sources.

Output structure:
  data/datasets/whisper_finetune/
    librispeech_clean100/
      audio/  (FLAC files)
      manifest.json
    librispeech_clean360/
      audio/
      manifest.json
    voxpopuli_en/
      audio/
      manifest.json
    common_voice_en/  (if HF token provided)
      audio/
      manifest.json
    combined_manifest.json  (all datasets merged)

Usage:
  python scripts/download_whisper_datasets.py
  python scripts/download_whisper_datasets.py --dataset librispeech100  (just one)
  python scripts/download_whisper_datasets.py --dataset voxpopuli
  python scripts/download_whisper_datasets.py --max-samples 50000  (limit per dataset)
  python scripts/download_whisper_datasets.py --hf-token YOUR_TOKEN  (for Common Voice)
"""

import os
import sys
import json
import time
import argparse
import logging
import soundfile as sf
import numpy as np
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("DatasetDownloader")

# Resolve project root
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_BASE = PROJECT_ROOT / "data" / "datasets" / "whisper_finetune"


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_progress(progress_file: Path) -> dict:
    """Load download progress for resume support."""
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {"completed": 0, "total": 0, "started": None, "last_update": None}


def save_progress(progress_file: Path, progress: dict):
    """Save download progress."""
    progress["last_update"] = datetime.now().isoformat()
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def _decode_audio_bytes(audio_dict):
    """Decode audio from HuggingFace sample, handling both auto-decoded and raw bytes."""
    import io
    # If already decoded (has 'array' key with data)
    if isinstance(audio_dict, dict) and 'array' in audio_dict:
        arr = audio_dict['array']
        if arr is not None and len(arr) > 0:
            return np.array(arr, dtype=np.float32), audio_dict.get('sampling_rate', 16000)
    # If raw bytes (has 'bytes' key)
    if isinstance(audio_dict, dict) and 'bytes' in audio_dict and audio_dict['bytes']:
        try:
            audio_np, sr = sf.read(io.BytesIO(audio_dict['bytes']), dtype='float32')
            return audio_np, sr
        except Exception:
            pass
    # If it's a path
    if isinstance(audio_dict, dict) and 'path' in audio_dict and audio_dict['path']:
        try:
            audio_np, sr = sf.read(audio_dict['path'], dtype='float32')
            return audio_np, sr
        except Exception:
            pass
    return None, None


def download_librispeech(split_name: str, hf_split: str, output_dir: Path, max_samples: int = 0):
    """
    Download LibriSpeech from HuggingFace (openslr/librispeech_asr).
    No account needed. CC BY 4.0 license.
    """
    from datasets import load_dataset
    
    audio_dir = ensure_dir(output_dir / "audio")
    manifest_file = output_dir / "manifest.json"
    progress_file = output_dir / "progress.json"
    
    progress = load_progress(progress_file)
    skip_count = progress["completed"]
    
    if skip_count > 0:
        logger.info(f"Resuming {split_name} from sample {skip_count}")
    
    logger.info(f"Loading LibriSpeech {split_name} via streaming (no auto-decode)...")
    # Load WITHOUT audio decoding to avoid torchcodec dependency (incompatible with PyTorch 2.2)
    from datasets import Audio
    ds = load_dataset("openslr/librispeech_asr", split=hf_split, streaming=True)
    ds = ds.cast_column("audio", Audio(decode=False))
    
    manifest = []
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
    
    count = skip_count
    skipped = 0
    errors = 0
    start_time = time.time()
    
    try:
        for i, sample in enumerate(ds):
            if i < skip_count:
                continue
            
            if max_samples > 0 and count >= max_samples:
                logger.info(f"Reached max_samples limit ({max_samples})")
                break
            
            text = sample.get("text", "")
            if not text:
                skipped += 1
                continue
            
            # Decode audio (handles both auto-decoded and raw bytes)
            audio_np, sr = _decode_audio_bytes(sample.get("audio", {}))
            if audio_np is None or len(audio_np) == 0:
                skipped += 1
                continue
            
            filename = f"ls_{split_name}_{count:07d}.flac"
            filepath = audio_dir / filename
            
            try:
                sf.write(str(filepath), audio_np, sr, format='FLAC')
            except Exception as e:
                errors += 1
                if errors < 5:
                    logger.warning(f"Write error sample {i}: {e}")
                continue
            
            manifest.append({
                "audio_path": f"audio/{filename}",
                "text": text.strip(),
                "duration": round(len(audio_np) / sr, 3),
                "sample_rate": sr,
                "source": f"librispeech_{split_name}",
                "speaker_id": str(sample.get("speaker_id", "")),
                "chapter_id": str(sample.get("chapter_id", "")),
            })
            
            count += 1
            
            if count % 500 == 0:
                elapsed = time.time() - start_time
                rate = (count - skip_count) / elapsed if elapsed > 0 else 0
                logger.info(f"  [{split_name}] {count:,} samples "
                           f"({rate:.1f}/sec, {skipped} skip, {errors} err)")
                
                progress["completed"] = count
                save_progress(progress_file, progress)
                with open(manifest_file, 'w') as f:
                    json.dump(manifest, f, indent=1)
    
    except KeyboardInterrupt:
        logger.warning("Download interrupted by user. Progress saved.")
    except Exception as e:
        logger.error(f"Error at sample {count}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        progress["completed"] = count
        save_progress(progress_file, progress)
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=1)
        
        elapsed = time.time() - start_time
        logger.info(f"  [{split_name}] DONE: {count:,} saved, "
                    f"{skipped} skipped, {errors} errors, {elapsed:.0f}s")
    
    return count


def download_voxpopuli(output_dir: Path, max_samples: int = 0):
    """
    Download VoxPopuli English from HuggingFace (facebook/voxpopuli).
    No account needed. CC0 license.
    European Parliament recordings — diverse European accents.
    """
    from datasets import load_dataset
    
    audio_dir = ensure_dir(output_dir / "audio")
    manifest_file = output_dir / "manifest.json"
    progress_file = output_dir / "progress.json"
    
    progress = load_progress(progress_file)
    skip_count = progress["completed"]
    
    if skip_count > 0:
        logger.info(f"Resuming VoxPopuli from sample {skip_count}")
    
    logger.info("Loading VoxPopuli English via streaming (no auto-decode)...")
    from datasets import Audio
    ds = load_dataset("facebook/voxpopuli", "en", split="train", streaming=True)
    ds = ds.cast_column("audio", Audio(decode=False))
    
    manifest = []
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
    
    count = skip_count
    skipped = 0
    start_time = time.time()
    
    errors = 0
    try:
        for i, sample in enumerate(ds):
            if i < skip_count:
                continue
            
            if max_samples > 0 and count >= max_samples:
                logger.info(f"Reached max_samples limit ({max_samples})")
                break
            
            text = sample.get("raw_text", "") or sample.get("normalized_text", "")
            if not text:
                skipped += 1
                continue
            
            audio_np, sr = _decode_audio_bytes(sample.get("audio", {}))
            if audio_np is None or len(audio_np) == 0:
                skipped += 1
                continue
            
            filename = f"vp_en_{count:07d}.flac"
            filepath = audio_dir / filename
            
            try:
                sf.write(str(filepath), audio_np, sr, format='FLAC')
            except Exception as e:
                errors += 1
                if errors < 5:
                    logger.warning(f"Write error sample {i}: {e}")
                continue
            
            manifest.append({
                "audio_path": f"audio/{filename}",
                "text": text.strip(),
                "duration": round(len(audio_np) / sr, 3),
                "sample_rate": sr,
                "source": "voxpopuli_en",
                "speaker_id": str(sample.get("speaker_id", "")),
            })
            
            count += 1
            
            if count % 500 == 0:
                elapsed = time.time() - start_time
                rate = (count - skip_count) / elapsed if elapsed > 0 else 0
                logger.info(f"  [voxpopuli] {count:,} samples "
                           f"({rate:.1f}/sec, {skipped} skip, {errors} err)")
                
                progress["completed"] = count
                save_progress(progress_file, progress)
                with open(manifest_file, 'w') as f:
                    json.dump(manifest, f, indent=1)
    
    except KeyboardInterrupt:
        logger.warning("Download interrupted. Progress saved.")
    except Exception as e:
        logger.error(f"Error at sample {count}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        progress["completed"] = count
        save_progress(progress_file, progress)
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=1)
        
        elapsed = time.time() - start_time
        logger.info(f"  [voxpopuli] DONE: {count:,} saved, "
                    f"{skipped} skipped, {errors} errors, {elapsed:.0f}s")
    
    return count


def download_common_voice(output_dir: Path, hf_token: str, max_samples: int = 0):
    """
    Download Common Voice 17 English from HuggingFace.
    REQUIRES HuggingFace account + token + terms acceptance.
    Best dataset for accent diversity (crowdsourced worldwide).
    """
    from datasets import load_dataset
    
    audio_dir = ensure_dir(output_dir / "audio")
    manifest_file = output_dir / "manifest.json"
    progress_file = output_dir / "progress.json"
    
    progress = load_progress(progress_file)
    skip_count = progress["completed"]
    
    logger.info("Loading Common Voice 17 English via streaming...")
    logger.info("(Requires HuggingFace account with terms accepted)")
    
    try:
        from datasets import Audio
        ds = load_dataset(
            "mozilla-foundation/common_voice_17_0", "en",
            split="train", streaming=True, token=hf_token
        )
        ds = ds.cast_column("audio", Audio(decode=False))
    except Exception as e:
        logger.error(f"Could not load Common Voice: {e}")
        logger.error("You need to: 1) Create a HuggingFace account, "
                     "2) Accept terms at https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0, "
                     "3) Generate a token at https://huggingface.co/settings/tokens")
        return 0
    
    manifest = []
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
    
    count = skip_count
    skipped = 0
    errors = 0
    start_time = time.time()
    
    try:
        for i, sample in enumerate(ds):
            if i < skip_count:
                continue
            
            if max_samples > 0 and count >= max_samples:
                break
            
            text = sample.get("sentence", "")
            if not text:
                skipped += 1
                continue
            
            audio_np, sr = _decode_audio_bytes(sample.get("audio", {}))
            if audio_np is None or len(audio_np) == 0:
                skipped += 1
                continue
            
            filename = f"cv_en_{count:07d}.flac"
            filepath = audio_dir / filename
            
            try:
                sf.write(str(filepath), audio_np, sr, format='FLAC')
            except Exception as e:
                errors += 1
                if errors < 5:
                    logger.warning(f"Write error sample {i}: {e}")
                continue
            
            manifest.append({
                "audio_path": f"audio/{filename}",
                "text": text.strip(),
                "duration": round(len(audio_np) / sr, 3),
                "sample_rate": sr,
                "source": "common_voice_en",
                "accent": sample.get("accent", ""),
                "age": sample.get("age", ""),
                "gender": sample.get("gender", ""),
            })
            
            count += 1
            
            if count % 500 == 0:
                elapsed = time.time() - start_time
                rate = (count - skip_count) / elapsed if elapsed > 0 else 0
                logger.info(f"  [common_voice] {count:,} samples "
                           f"({rate:.1f}/sec, {skipped} skip, {errors} err)")
                
                progress["completed"] = count
                save_progress(progress_file, progress)
                with open(manifest_file, 'w') as f:
                    json.dump(manifest, f, indent=1)
    
    except KeyboardInterrupt:
        logger.warning("Download interrupted. Progress saved.")
    except Exception as e:
        logger.error(f"Error at sample {count}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        progress["completed"] = count
        save_progress(progress_file, progress)
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=1)
        
        elapsed = time.time() - start_time
        logger.info(f"  [common_voice] DONE: {count:,} saved, "
                    f"{skipped} skipped, {errors} errors, {elapsed:.0f}s")
    
    return count


def merge_manifests(base_dir: Path):
    """Merge all individual manifests into one combined manifest."""
    combined = []
    
    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            manifest_file = subdir / "manifest.json"
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    entries = json.load(f)
                # Fix paths to be relative to base_dir
                for entry in entries:
                    entry["audio_path"] = f"{subdir.name}/{entry['audio_path']}"
                combined.extend(entries)
                logger.info(f"  Merged {len(entries):,} entries from {subdir.name}")
    
    combined_file = base_dir / "combined_manifest.json"
    with open(combined_file, 'w') as f:
        json.dump(combined, f, indent=1)
    
    # Also create a stats summary
    total_duration = sum(e.get("duration", 0) for e in combined)
    sources = {}
    for e in combined:
        src = e.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    
    stats = {
        "total_samples": len(combined),
        "total_duration_hours": round(total_duration / 3600, 1),
        "sources": sources,
        "created": datetime.now().isoformat(),
    }
    
    stats_file = base_dir / "dataset_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"COMBINED DATASET SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total samples: {len(combined):,}")
    logger.info(f"Total duration: {total_duration/3600:.1f} hours")
    for src, cnt in sorted(sources.items()):
        logger.info(f"  {src}: {cnt:,} samples")
    logger.info(f"Manifest: {combined_file}")
    logger.info(f"Stats: {stats_file}")
    
    return len(combined)


def main():
    parser = argparse.ArgumentParser(description="Download speech datasets for Whisper fine-tuning")
    parser.add_argument("--dataset", choices=[
        "librispeech100", "librispeech360", "librispeech500",
        "voxpopuli", "common_voice", "all"
    ], default="all", help="Which dataset to download (default: all free datasets)")
    parser.add_argument("--max-samples", type=int, default=0,
                       help="Max samples per dataset (0 = all)")
    parser.add_argument("--hf-token", type=str, default="",
                       help="HuggingFace token for Common Voice (optional)")
    parser.add_argument("--merge-only", action="store_true",
                       help="Only merge existing manifests, don't download")
    args = parser.parse_args()
    
    ensure_dir(OUTPUT_BASE)
    
    if args.merge_only:
        merge_manifests(OUTPUT_BASE)
        return
    
    total_samples = 0
    
    logger.info("="*60)
    logger.info("Monica AI — Whisper Fine-Tuning Dataset Downloader")
    logger.info("="*60)
    logger.info(f"Output directory: {OUTPUT_BASE}")
    logger.info(f"Dataset: {args.dataset}")
    if args.max_samples > 0:
        logger.info(f"Max samples per dataset: {args.max_samples:,}")
    logger.info("")
    
    # LibriSpeech train-clean-100 (~28k samples)
    if args.dataset in ("librispeech100", "all"):
        logger.info("--- LibriSpeech train-clean-100 ---")
        logger.info("US English read speech, ~28,539 samples, CC BY 4.0")
        out = ensure_dir(OUTPUT_BASE / "librispeech_clean100")
        n = download_librispeech("clean100", "train.clean.100", out, args.max_samples)
        total_samples += n
        logger.info("")
    
    # LibriSpeech train-clean-360 (~104k samples)
    if args.dataset in ("librispeech360", "all"):
        logger.info("--- LibriSpeech train-clean-360 ---")
        logger.info("US English read speech, ~104,014 samples, CC BY 4.0")
        out = ensure_dir(OUTPUT_BASE / "librispeech_clean360")
        n = download_librispeech("clean360", "train.clean.360", out, args.max_samples)
        total_samples += n
        logger.info("")
    
    # LibriSpeech train-other-500 (~149k samples, noisier/more diverse)
    if args.dataset in ("librispeech500",):
        logger.info("--- LibriSpeech train-other-500 ---")
        logger.info("US English read speech (noisier), ~148,688 samples, CC BY 4.0")
        out = ensure_dir(OUTPUT_BASE / "librispeech_other500")
        n = download_librispeech("other500", "train.other.500", out, args.max_samples)
        total_samples += n
        logger.info("")
    
    # VoxPopuli English (~180k+ samples, European accents)
    if args.dataset in ("voxpopuli", "all"):
        logger.info("--- VoxPopuli English ---")
        logger.info("European Parliament recordings, diverse accents, CC0")
        out = ensure_dir(OUTPUT_BASE / "voxpopuli_en")
        n = download_voxpopuli(out, args.max_samples)
        total_samples += n
        logger.info("")
    
    # Common Voice English (requires HF token)
    if args.dataset in ("common_voice", "all") and args.hf_token:
        logger.info("--- Common Voice 17 English ---")
        logger.info("Global crowdsourced speech, diverse accents, CC-0")
        out = ensure_dir(OUTPUT_BASE / "common_voice_en")
        n = download_common_voice(out, args.hf_token, args.max_samples)
        total_samples += n
        logger.info("")
    elif args.dataset in ("common_voice", "all") and not args.hf_token:
        logger.info("--- Common Voice 17 English --- SKIPPED (no --hf-token)")
        logger.info("To download, provide --hf-token YOUR_TOKEN")
        logger.info("Get token: https://huggingface.co/settings/tokens")
        logger.info("")
    
    # Merge all manifests
    if total_samples > 0:
        logger.info("--- Merging all manifests ---")
        merge_manifests(OUTPUT_BASE)
    
    logger.info(f"\nTotal samples downloaded this session: {total_samples:,}")
    logger.info("Download complete! Run the Whisper fine-tuning script next:")
    logger.info("  python scripts/finetune_whisper.py")


if __name__ == "__main__":
    main()
