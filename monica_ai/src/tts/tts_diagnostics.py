"""
TTS Diagnostics Module for Monica AI
Provides self-diagnosis capabilities for TTS system issues
"""
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TTSDiagnostics:
    """Diagnose TTS system issues and provide actionable solutions."""

    def __init__(self, tts_manager=None):
        """Initialize diagnostics with optional TTS manager reference."""
        self.tts_manager = tts_manager
        self.results = {}

    def run_full_diagnosis(self) -> Dict[str, any]:
        """Run complete TTS system diagnosis."""
        print("\n" + "="*60)
        print("MONICA TTS DIAGNOSTICS")
        print("="*60 + "\n")

        results = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'checks': {},
            'issues': [],
            'solutions': []
        }

        # Check 1: XTTS Configuration
        results['checks']['xtts_config'] = self._check_xtts_configuration()

        # Check 2: Model Files
        results['checks']['model_files'] = self._check_model_files()

        # Check 3: GPU/CUDA Status
        results['checks']['gpu_status'] = self._check_gpu_status()

        # Check 4: Audio System
        results['checks']['audio_system'] = self._check_audio_system()

        # Check 5: TTS Manager State
        if self.tts_manager:
            results['checks']['tts_manager_state'] = self._check_tts_manager_state()

        # Check 6: Dependencies
        results['checks']['dependencies'] = self._check_dependencies()

        # Check 7: Anti-Barge-In Settings
        if self.tts_manager:
            results['checks']['anti_barge_in'] = self._check_anti_barge_in()

        # Analyze results and generate solutions
        self._analyze_results(results)

        # Display report
        self._display_report(results)

        self.results = results
        return results

    def _check_xtts_configuration(self) -> Dict:
        """Check XTTS configuration settings."""
        result = {'status': 'unknown', 'details': {}}

        try:
            from monica_ai.src.config.settings import config

            result['details']['use_monica_tts'] = getattr(config, 'USE_MONICA_TTS', False)
            result['details']['tts_engine'] = getattr(config, 'TTS_ENGINE', 'unknown')
            result['details']['xtts_checkpoint'] = getattr(config, 'XTTS_CHECKPOINT', None)
            result['details']['xtts_speaker_wav'] = getattr(config, 'XTTS_SPEAKER_WAV', None)

            if result['details']['use_monica_tts']:
                result['status'] = 'enabled'
            else:
                result['status'] = 'disabled'
                result['issue'] = "Monica TTS is disabled in configuration"
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def _check_model_files(self) -> Dict:
        """Check for trained model files and checkpoints."""
        result = {'status': 'unknown', 'details': {}, 'found_models': []}

        try:
            from monica_ai.src.audio.monica_tts import MonicaTTS

            # Check for training directories
            base_dir = Path(__file__).parent.parent.parent.parent
            training_data = base_dir / "data" / "training"
            training_root = training_data / "monica_tts_training" / "models" / "xtts_official_trained" / "run" / "training"
            accent_tune_root = training_data / "monica_tts_training" / "models" / "xtts_official_trained" / "run" / "accent_tune"

            result['details']['training_root_exists'] = training_root.exists()
            result['details']['accent_tune_root_exists'] = accent_tune_root.exists()

            # Look for checkpoints
            if accent_tune_root.exists():
                for run_dir in accent_tune_root.glob("**/GPT_XTTS_Monica_AccentTune-*"):
                    for model in run_dir.glob("best_model*.pth"):
                        result['found_models'].append({
                            'path': str(model),
                            'type': 'accent_tune',
                            'size_mb': model.stat().st_size / (1024*1024)
                        })

            if training_root.exists():
                for run_dir in training_root.glob("GPT_XTTS_Monica-*"):
                    for model in run_dir.glob("best_model*.pth"):
                        result['found_models'].append({
                            'path': str(model),
                            'type': 'training',
                            'size_mb': model.stat().st_size / (1024*1024)
                        })

            # Check for reference WAV files
            voice_dir = training_data / "voice_training" / "recordings" / "MJP"
            if voice_dir.exists():
                wav_files = list(voice_dir.glob("*.wav"))
                result['details']['reference_wavs'] = len(wav_files)
                result['details']['voice_dir'] = str(voice_dir)
            else:
                result['details']['reference_wavs'] = 0
                result['issue'] = f"Voice training directory not found: {voice_dir}"

            if result['found_models']:
                result['status'] = 'ok'
            else:
                result['status'] = 'missing'
                result['issue'] = "No trained XTTS checkpoints found"

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def _check_gpu_status(self) -> Dict:
        """Check GPU and CUDA availability."""
        result = {'status': 'unknown', 'details': {}}

        try:
            import torch
            result['details']['pytorch_available'] = True
            result['details']['cuda_available'] = torch.cuda.is_available()

            if torch.cuda.is_available():
                result['details']['cuda_version'] = torch.version.cuda
                result['details']['gpu_name'] = torch.cuda.get_device_name(0)
                result['details']['gpu_memory_total'] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                result['details']['gpu_memory_allocated'] = torch.cuda.memory_allocated(0) / (1024**3)
                result['status'] = 'ok'
            else:
                result['status'] = 'cpu_only'
                result['issue'] = "CUDA not available - using CPU (much slower)"

        except ImportError:
            result['status'] = 'missing'
            result['details']['pytorch_available'] = False
            result['issue'] = "PyTorch not installed"
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def _check_audio_system(self) -> Dict:
        """Check audio playback system."""
        result = {'status': 'unknown', 'details': {}}

        try:
            import sounddevice as sd
            result['details']['sounddevice_available'] = True
            result['details']['default_output_device'] = sd.default.device[1]

            # Get device info
            device_info = sd.query_devices(sd.default.device[1])
            result['details']['output_device_name'] = device_info['name']
            result['details']['output_sample_rate'] = device_info['default_samplerate']

            result['status'] = 'ok'

        except ImportError:
            result['status'] = 'missing'
            result['details']['sounddevice_available'] = False
            result['issue'] = "sounddevice not installed"
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def _check_tts_manager_state(self) -> Dict:
        """Check TTS manager current state."""
        result = {'status': 'unknown', 'details': {}}

        if not self.tts_manager:
            result['status'] = 'unavailable'
            return result

        try:
            tm = self.tts_manager
            result['details']['is_initialized'] = tm.is_initialized
            result['details']['engine_type'] = tm.engine_type
            result['details']['use_monica_tts'] = tm.use_monica_tts
            result['details']['is_speaking'] = tm.is_speaking
            result['details']['sample_rate'] = tm.sample_rate

            # Check if Monica TTS is actually loaded
            result['details']['monica_tts_loaded'] = False
            try:
                from monica_ai.src.tts.tts_manager import _monica_tts_instance, MONICA_TTS_AVAILABLE
                result['details']['monica_tts_loaded'] = _monica_tts_instance is not None
                result['details']['monica_tts_available'] = MONICA_TTS_AVAILABLE
            except:
                pass

            if tm.use_monica_tts and not result['details']['monica_tts_loaded']:
                result['status'] = 'fallback'
                result['issue'] = f"Monica TTS enabled but not loaded - using {tm.engine_type} instead"
            else:
                result['status'] = 'ok'

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def _check_dependencies(self) -> Dict:
        """Check required dependencies."""
        result = {'status': 'unknown', 'dependencies': {}}

        deps = {
            'torch': 'PyTorch',
            'torchaudio': 'TorchAudio',
            'TTS': 'Coqui TTS',
            'sounddevice': 'SoundDevice',
            'scipy': 'SciPy',
            'num2words': 'num2words',
        }

        missing = []
        for module, name in deps.items():
            try:
                __import__(module)
                result['dependencies'][name] = 'installed'
            except ImportError:
                result['dependencies'][name] = 'missing'
                missing.append(name)

        if missing:
            result['status'] = 'incomplete'
            result['missing'] = missing
        else:
            result['status'] = 'complete'

        return result

    def _check_anti_barge_in(self) -> Dict:
        """Check anti-barge-in settings that might cause cutoffs."""
        result = {'status': 'unknown', 'details': {}}

        if not self.tts_manager:
            result['status'] = 'unavailable'
            return result

        try:
            tm = self.tts_manager
            result['details']['enable_anti_barge_in'] = tm.enable_anti_barge_in
            result['details']['stop_on_user_speech'] = tm.stop_on_user_speech
            result['details']['required_silence_ms'] = tm.required_silence_ms
            result['details']['required_speaking_to_stop'] = 0.8  # From code

            # Check if these settings might cause issues
            if tm.enable_anti_barge_in and tm.stop_on_user_speech:
                result['status'] = 'aggressive'
                result['issue'] = "Anti-barge-in is very aggressive (stops after 0.8s of detected speech)"
            else:
                result['status'] = 'ok'

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def _analyze_results(self, results: Dict):
        """Analyze diagnostic results and generate solutions."""
        checks = results['checks']
        issues = results['issues']
        solutions = results['solutions']

        # Issue: Monica TTS not loading
        if checks.get('tts_manager_state', {}).get('status') == 'fallback':
            issues.append({
                'severity': 'high',
                'title': 'Monica TTS Not Loading - Reverting to Piper',
                'description': 'Monica is configured to use XTTS but falls back to Piper for speech'
            })
            solutions.append({
                'issue': 'Monica TTS Not Loading',
                'steps': [
                    '1. Check that trained XTTS models exist in monica_tts_training/models/',
                    '2. Verify GPU/CUDA is available (XTTS requires significant compute)',
                    '3. Check for error messages during MonicaTTS initialization',
                    '4. Ensure reference WAV files exist in voice_training/recordings/MJP/',
                    '5. Try running: MONICA_TTS_DEBUG=1 to see detailed loading errors'
                ]
            })

        # Issue: Missing models
        if checks.get('model_files', {}).get('status') == 'missing':
            issues.append({
                'severity': 'high',
                'title': 'No Trained XTTS Models Found',
                'description': 'No trained model checkpoints detected in expected locations'
            })
            solutions.append({
                'issue': 'No Trained XTTS Models',
                'steps': [
                    '1. Train the XTTS model using: python train_wav2vec2_final.py',
                    '2. Or check if models are in a different location',
                    '3. Set MONICA_XTTS_CHECKPOINT environment variable to model path',
                    '4. Verify training completed successfully without errors'
                ]
            })

        # Issue: Aggressive anti-barge-in
        if checks.get('anti_barge_in', {}).get('status') == 'aggressive':
            issues.append({
                'severity': 'medium',
                'title': 'Aggressive Anti-Barge-In Causing Cutoffs',
                'description': 'Monica stops speaking after detecting 0.8s of user speech'
            })
            solutions.append({
                'issue': 'Mid-Sentence Cutoff',
                'steps': [
                    '1. Disable stop_on_user_speech: tts_manager.stop_on_user_speech = False',
                    '2. Or increase required_speaking_to_stop threshold in tts_manager.py line 1880',
                    '3. Or disable anti-barge-in entirely: tts_manager.enable_anti_barge_in = False',
                    '4. Check microphone sensitivity - background noise may trigger false detection'
                ]
            })

        # Issue: GPU not available
        if checks.get('gpu_status', {}).get('status') == 'cpu_only':
            issues.append({
                'severity': 'medium',
                'title': 'CUDA Not Available - Slow Performance',
                'description': 'XTTS will run on CPU which causes long delays'
            })
            solutions.append({
                'issue': 'Long Delay Before Voice Response',
                'steps': [
                    '1. Install CUDA-enabled PyTorch: pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118',
                    '2. Verify NVIDIA GPU drivers are installed and up to date',
                    '3. Check CUDA installation: nvidia-smi',
                    '4. Or accept longer delays when using CPU-only mode'
                ]
            })

    def _display_report(self, results: Dict):
        """Display diagnostic report to console."""
        print("\n📊 DIAGNOSTIC RESULTS")
        print("-" * 60)

        for check_name, check_result in results['checks'].items():
            status = check_result.get('status', 'unknown')
            status_symbol = {
                'ok': '✅',
                'enabled': '✅',
                'complete': '✅',
                'disabled': '⚠️',
                'cpu_only': '⚠️',
                'aggressive': '⚠️',
                'fallback': '❌',
                'missing': '❌',
                'incomplete': '❌',
                'error': '❌',
                'unknown': '❓'
            }.get(status, '❓')

            print(f"{status_symbol} {check_name.replace('_', ' ').title()}: {status}")

            if 'issue' in check_result:
                print(f"   Issue: {check_result['issue']}")

        # Display issues and solutions
        if results['issues']:
            print("\n\n🚨 IDENTIFIED ISSUES")
            print("-" * 60)
            for i, issue in enumerate(results['issues'], 1):
                severity_symbol = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(issue['severity'], '⚪')
                print(f"\n{severity_symbol} Issue #{i}: {issue['title']}")
                print(f"   {issue['description']}")

        if results['solutions']:
            print("\n\n💡 RECOMMENDED SOLUTIONS")
            print("-" * 60)
            for i, solution in enumerate(results['solutions'], 1):
                print(f"\n{i}. {solution['issue']}:")
                for step in solution['steps']:
                    print(f"   {step}")

        print("\n" + "="*60 + "\n")

    def diagnose_slow_response(self) -> str:
        """Quick diagnosis for slow TTS response."""
        report = []
        report.append("Diagnosing slow TTS response...")

        # Check GPU
        try:
            import torch
            if not torch.cuda.is_available():
                report.append("❌ CUDA not available - XTTS is running on CPU (very slow)")
                report.append("   Solution: Install CUDA-enabled PyTorch")
            else:
                report.append("✅ GPU available")
        except:
            report.append("❌ PyTorch not installed")

        # Check if using streaming
        if self.tts_manager:
            if self.tts_manager.use_monica_tts:
                report.append("✅ Monica XTTS enabled (supports streaming)")
            else:
                report.append(f"⚠️ Using {self.tts_manager.engine_type} instead of Monica XTTS")

        # Check anti-barge-in delays
        if self.tts_manager and self.tts_manager.enable_anti_barge_in:
            silence_ms = self.tts_manager.required_silence_ms
            report.append(f"⚠️ Anti-barge-in adds up to {silence_ms}ms delay waiting for silence")
            report.append(f"   Plus up to 2000ms max wait if input is noisy")

        return "\n".join(report)

    def diagnose_cutoff(self) -> str:
        """Quick diagnosis for mid-sentence cutoffs."""
        report = []
        report.append("Diagnosing mid-sentence cutoffs...")

        if not self.tts_manager:
            return "TTS Manager not available for diagnosis"

        tm = self.tts_manager

        if tm.enable_anti_barge_in and tm.stop_on_user_speech:
            report.append("❌ Anti-barge-in is stopping playback when user speech detected")
            report.append("   Monica stops after 0.8s of detected user speech")
            report.append("   Solution: Set tts_manager.stop_on_user_speech = False")

        # Check text splitting
        report.append(f"ℹ️  Text is split into chunks of max 220 characters")
        report.append(f"ℹ️  0.12s pause between chunks (may cause unnatural pauses)")

        return "\n".join(report)


# Convenience function for quick diagnosis
def quick_diagnosis(tts_manager=None) -> str:
    """Run quick diagnosis and return text report."""
    diag = TTSDiagnostics(tts_manager)
    results = diag.run_full_diagnosis()
    return "Diagnosis complete. See console output above."
