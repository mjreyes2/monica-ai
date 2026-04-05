"""
Patch transformers and torch.load to allow loading models with current PyTorch version.
This must be imported BEFORE any transformers/speechbrain/TTS imports.

PyTorch 2.6 changed torch.load default to weights_only=True which breaks TTS/XTTS loading.
"""

def patch_torch_load():
    """Patch torch.load to default weights_only=False for TTS compatibility."""
    try:
        import torch
        _original_torch_load = torch.load
        
        def patched_torch_load(*args, **kwargs):
            # Default weights_only to False if not specified (PyTorch 2.6+ compatibility)
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return _original_torch_load(*args, **kwargs)
        
        torch.load = patched_torch_load
        print(f"[TORCH-PATCH] [OK] Patched torch.load for PyTorch {torch.__version__} (weights_only=False default)")
        return True
    except Exception as e:
        print(f"[TORCH-PATCH] [WARN] torch.load patch failed: {e}")
        return False

def patch_transformers():
    """Patch transformers to skip torch.load safety check for local models (version-safe)."""
    try:
        import transformers
        import transformers.utils.import_utils as import_utils

        tfm_version = getattr(transformers, "__version__", "unknown")

        # Only patch if the symbol exists in this Transformers version
        if hasattr(import_utils, "check_torch_load_is_safe"):
            # Save original function (not used, but kept for potential future restore)
            _original_check = import_utils.check_torch_load_is_safe  # noqa: F841

            # Create patched version that does nothing (accepts any signature)
            def patched_check(*args, **kwargs):
                # Skip the safety check - we trust our locally trained models
                return None

            import_utils.check_torch_load_is_safe = patched_check
            print(f"[TORCH-PATCH] [OK] Bypassed check_torch_load_is_safe (Transformers {tfm_version})")
            return True
        else:
            # Newer/other versions may not expose this function; nothing to patch
            print(f"[TORCH-PATCH] [SKIP] No 'check_torch_load_is_safe' in Transformers {tfm_version}; nothing to patch")
            return True

    except Exception as e:
        # Non-fatal: just skip patching
        print(f"[TORCH-PATCH] [WARN] Patch not applied: {e}")
        return False

def patch_torchaudio():
    """Patch torchaudio to ensure list_audio_backends is available for speechbrain compatibility."""
    try:
        import torchaudio
        if not hasattr(torchaudio, 'list_audio_backends'):
            def list_audio_backends():
                return ['soundfile']  # Safe default
            torchaudio.list_audio_backends = list_audio_backends
            print(f"[TORCH-PATCH] [OK] Added list_audio_backends to torchaudio {torchaudio.__version__}")
        else:
            print(f"[TORCH-PATCH] [OK] torchaudio.list_audio_backends already exists")
        return True
    except Exception as e:
        print(f"[TORCH-PATCH] [WARN] torchaudio patch failed: {e}")
        return False

# Apply patches immediately on import
patch_torch_load()  # MUST be first - patches torch.load for TTS/XTTS
patch_transformers()
patch_torchaudio()  # Ensure torchaudio has list_audio_backends
