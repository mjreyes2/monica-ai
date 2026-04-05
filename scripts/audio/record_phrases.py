import sounddevice as sd
import soundfile as sf
import os
import numpy as np

# Output directory - UNIFIED with Monica GUI recordings
# All recordings go to the same location for training
OUTPUT_DIR = "voice_training/recordings/MJP"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample rate
SAMPLE_RATE = 16000

# Set audio devices - Maono mic for input, Maono speakers for direct output
# Device 11 = Speakers (Maono ProStudio 2x2 Lite) - direct to your monitors
sd.default.device = (1, 11)  # (input: Maono mic, output: Maono speakers directly)

# Load phrases from file
with open("phrases.txt", "r", encoding="utf-8") as f:
    phrases = [line.strip() for line in f if line.strip()]

def record_audio(duration=6):
    print("   Recording...")
    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    print("   Done recording")
    return audio

def save_audio(audio, filename):
    sf.write(filename, audio, SAMPLE_RATE)

def play_audio(filename):
    if os.path.exists(filename):
        data, fs = sf.read(filename)
        print("   Playing...")
        sd.play(data, fs)
        sd.wait()
        print("   Done playing")
    else:
        print("   No recording found")

def get_filename(i, phrase):
    safe_phrase = phrase.replace(" ", "_").replace("'", "").replace(",", "")[:50]
    return os.path.join(OUTPUT_DIR, f"{i+1:04d}_{safe_phrase}.wav")

print("="*60)
print("VOICE RECORDING SESSION")
print("="*60)
print(f"Total phrases: {len(phrases)}")
print()
print("Commands:")
print("  ENTER  = Record phrase (6 sec)")
print("  p      = Play last recording")
print("  r      = Re-record current phrase")
print("  s      = Skip phrase")
print("  g NUM  = Go to phrase number (e.g. 'g 50')")
print("  q      = Quit")
print("="*60)

i = 0
while i < len(phrases):
    phrase = phrases[i]
    filename = get_filename(i, phrase)
    exists = "" if os.path.exists(filename) else ""
    
    print(f"\n[{i+1}/{len(phrases)}] {exists} SAY: {phrase}")
    cmd = input("> ").strip().lower()
    
    if cmd == 'q' or cmd == 'quit':
        print("Exiting...")
        break
    elif cmd == 's' or cmd == 'skip':
        print("  Skipped.")
        i += 1
        continue
    elif cmd == 'p' or cmd == 'play':
        play_audio(filename)
        continue  # Stay on same phrase
    elif cmd == 'r' or cmd == 'redo':
        # Re-record current phrase
        audio = record_audio()
        save_audio(audio, filename)
        print(f"  Saved: {filename}")
        continue  # Stay on same phrase to review
    elif cmd.startswith('g '):
        try:
            num = int(cmd.split()[1])
            if 1 <= num <= len(phrases):
                i = num - 1
                print(f"  Jumped to phrase {num}")
            else:
                print(f"  Invalid number. Enter 1-{len(phrases)}")
        except:
            print("  Usage: g NUM (e.g. 'g 50')")
        continue
    elif cmd == '':
        # Record
        audio = record_audio()
        save_audio(audio, filename)
        print(f"  Saved: {filename}")
        i += 1
    else:
        print("  Unknown command. Use ENTER, p, r, s, g NUM, or q")

print("\nRecording session complete!")
