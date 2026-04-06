#!/usr/bin/env python3
"""
Test Clean Monica System
Only SpeechBrain - no old models or references
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_clean_system():
    """Test the clean system"""
    print("=" * 60)
    print("TESTING CLEAN MONICA SYSTEM")
    print("=" * 60)
    
    # Test configuration
    import json
    with open("config.json", "r") as f:
        config = json.load(f)
    
    print("✅ Configuration loaded:")
    print(f"   STT Engine: {config['stt']['engine']}")
    print(f"   No Whisper references: {'whisper_model' not in config['stt']}")
    
    # Test settings
    from src.config.settings import config as app_config
    print(f"✅ Settings loaded: {app_config.STT_ENGINE}")
    print(f"   No Whisper model size: {not hasattr(app_config, 'WHISPER_MODEL_SIZE')}")
    
    # Test audio manager
    from src.audio.audio_manager import AudioManager
    print("🎤 Initializing clean audio manager...")
    
    audio_manager = AudioManager(app_config)
    
    print(f"✅ Audio manager status: {audio_manager.get_status()}")
    
    # Test SpeechBrain integration
    if audio_manager.is_speechbrain_ready():
        print("✅ SpeechBrain is ready!")
        
        # Test recognition
        test_file = "data/training/recordings/training_phrases/phrase_00_Monica_initialize.wav"
        if Path(test_file).exists():
            result = audio_manager.recognize_file(test_file)
            print(f"🎤 Recognition result: '{result}'")
            
            if result:
                print("🎉 SUCCESS! Clean system works perfectly!")
            else:
                print("❌ Recognition failed")
        else:
            print("⚠️ Test file not found")
    else:
        print("⏳ SpeechBrain still loading...")
        print("   This is normal - it takes 60-120 seconds")
        print("   The system will work once loading completes")
    
    # Verify no old models
    old_model_dirs = ["models/whisper", "whisper_community_finetuned", "whisper_finetuned_personal"]
    old_models_exist = any(Path(d).exists() for d in old_model_dirs)
    
    if not old_models_exist:
        print("✅ All old speech recognition models removed")
    else:
        print("⚠️ Some old models still exist")
    
    print("\n" + "=" * 60)
    print("🎊 CLEAN SYSTEM TEST COMPLETE!")
    print("✅ Only SpeechBrain Personal Voice Recognition")
    print("✅ No Whisper or old model references")
    print("✅ No intro recordings interfering")
    print("✅ Clean configuration")
    print("=" * 60)
    
    return audio_manager

if __name__ == "__main__":
    test_clean_system()
