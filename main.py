# main.py
import logging
import os
import sys
import warnings
from pathlib import Path


def _configure_startup_environment() -> None:
    """Set logging and warning controls before heavy imports."""
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
    os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
    os.environ.setdefault('OPENCV_VIDEOIO_DEBUG', '0')
    os.environ.setdefault('OPENCV_LOG_LEVEL', 'ERROR')
    os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings(
        'ignore',
        category=UserWarning,
        message=r"Module 'speechbrain\..*' was deprecated, redirecting to '.*'\. Please update your script.*",
    )
    warnings.filterwarnings('ignore', module='pygame.pkgdata')
    warnings.filterwarnings('ignore', message='.*pkg_resources.*deprecated.*')

    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    logging.getLogger('absl').setLevel(logging.ERROR)


_configure_startup_environment()

# ── Torch DLL fix: must run before any torch import ──
_torch_lib = Path(sys.prefix) / "Lib" / "site-packages" / "torch" / "lib"
if _torch_lib.is_dir():
    os.add_dll_directory(str(_torch_lib))

# ── SpeechBrain lazy-import fix ──
# SpeechBrain 1.x uses LazyModule for optional integrations (k2_fsa, huggingface
# wordemb, etc.). When ANY optional dep is missing, the LazyModule raises an
# ImportError that propagates and breaks unrelated imports (TTS, transformers).
# Patch LazyModule.ensure_module to suppress failures for optional integrations.
def _patch_speechbrain_lazy():
    try:
        from speechbrain.utils.importutils import LazyModule
        _orig_ensure = LazyModule.ensure_module

        def _safe_ensure(self, stacklevel=1):
            try:
                return _orig_ensure(self, stacklevel + 1)
            except (ImportError, Exception):
                # Return a dummy module so attribute access doesn't crash
                if self.lazy_module is None:
                    import types as _t
                    self.lazy_module = _t.ModuleType(self.target)
                return self.lazy_module

        LazyModule.ensure_module = _safe_ensure
    except Exception:
        pass

_patch_speechbrain_lazy()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.monica_services_launcher import launch_monica

if __name__ == '__main__':
    launch_monica()
