  #!/usr/bin/env python3

"""

STT Training Recorder

Records your voice reading phrases for speech-to-text training.

Press SPACE to start/stop recording, ENTER to skip, Q to quit.

"""



import os

import sys

import time

import wave

import threading

import textwrap

from pathlib import Path

from datetime import datetime



# Check for required packages

try:

    import pyaudio

    HAS_PYAUDIO = True

except ImportError:

    HAS_PYAUDIO = False

    print("ERROR: pyaudio not installed. Run: pip install pyaudio")



try:

    import keyboard

    HAS_KEYBOARD = True

except ImportError:

    HAS_KEYBOARD = False

    print("ERROR: keyboard not installed. Run: pip install keyboard")



# Paths

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # scripts/audio -> scripts -> monica_project

PHRASES_FILE = PROJECT_ROOT / "data" / "training" / "stt_training_phrases.txt"

OUTPUT_DIR = PROJECT_ROOT / "data" / "training" / "personal_voice_model" / "stt_training_recordings"

PROGRESS_FILE = OUTPUT_DIR / "progress.txt"



# Audio settings

SAMPLE_RATE = 16000

CHANNELS = 1

CHUNK = 1024

FORMAT = pyaudio.paInt16 if HAS_PYAUDIO else None





class STTRecorder:

    def __init__(self):

        self.phrases = []

        self.current_index = 0

        self.is_recording = False

        self.audio_frames = []

        self.audio = None

        self.stream = None

        self.running = True

        self.last_recording = None  # Track last saved file for playback

        self.pending_save = False  # Track if we need to confirm a recording

        self.input_device = None  # Microphone device index

        self.output_device = None  # Speaker device index

        

        # Create output directory

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        

        # Select audio devices

        self._select_audio_devices()

        

        # Load phrases

        self._load_phrases()

        

        # Load progress

        self._load_progress()

        

    def _select_audio_devices(self):

        """Let user select input/output audio devices"""

        audio = pyaudio.PyAudio()

        

        print("\n" + "=" * 60)

        print("   AUDIO DEVICE SETUP")

        print("=" * 60)

        

        # List input devices (microphones)

        print("\n  INPUT DEVICES (Microphones):")

        input_devices = []

        for i in range(audio.get_device_count()):

            info = audio.get_device_info_by_index(i)

            if info['maxInputChannels'] > 0:

                input_devices.append((i, info['name']))

                print(f"    [{len(input_devices)-1}] {info['name']}")

        

        # List output devices (speakers)

        print("\n  OUTPUT DEVICES (Speakers):")

        output_devices = []

        for i in range(audio.get_device_count()):

            info = audio.get_device_info_by_index(i)

            if info['maxOutputChannels'] > 0:

                output_devices.append((i, info['name']))

                print(f"    [{len(output_devices)-1}] {info['name']}")

        

        # Select input device

        print("\n  Select MICROPHONE (or press ENTER for default):")

        try:

            choice = input("  > ").strip()

            if choice and choice.isdigit():

                idx = int(choice)

                if 0 <= idx < len(input_devices):

                    self.input_device = input_devices[idx][0]

                    print(f"   Using: {input_devices[idx][1]}")

        except:

            pass

        

        # Select output device

        print("\n  Select SPEAKERS (or press ENTER for default):")

        try:

            choice = input("  > ").strip()

            if choice and choice.isdigit():

                idx = int(choice)

                if 0 <= idx < len(output_devices):

                    self.output_device = output_devices[idx][0]

                    print(f"   Using: {output_devices[idx][1]}")

        except:

            pass

        

        audio.terminate()

        print()

        

    def _load_phrases(self):

        """Load training phrases from file"""

        if not PHRASES_FILE.exists():

            print(f"ERROR: Phrases file not found: {PHRASES_FILE}")

            sys.exit(1)

            

        with open(PHRASES_FILE, 'r', encoding='utf-8') as f:

            self.phrases = [line.strip() for line in f if line.strip()]

        

        print(f"Loaded {len(self.phrases)} phrases")

        

    def _load_progress(self):

        """Load recording progress"""

        if PROGRESS_FILE.exists():

            try:

                with open(PROGRESS_FILE, 'r') as f:

                    self.current_index = int(f.read().strip())

                print(f"Resuming from phrase {self.current_index + 1}")

                

                # Find the most recent recording file

                recordings = list(OUTPUT_DIR.glob("phrase_*.wav"))

                if recordings:

                    self.last_recording = max(recordings, key=lambda f: f.stat().st_mtime)

                    print(f"Last recording: {self.last_recording.name}")

            except:

                self.current_index = 0

                

    def _save_progress(self):

        """Save recording progress"""

        with open(PROGRESS_FILE, 'w') as f:

            f.write(str(self.current_index))

            

    def _record_audio(self):

        """Record audio in background thread"""

        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(

            format=FORMAT,

            channels=CHANNELS,

            rate=SAMPLE_RATE,

            input=True,

            input_device_index=self.input_device,

            frames_per_buffer=CHUNK

        )

        

        self.audio_frames = []

        while self.is_recording:

            try:

                data = self.stream.read(CHUNK, exception_on_overflow=False)

                self.audio_frames.append(data)

            except:

                break

                

        self.stream.stop_stream()

        self.stream.close()

        self.audio.terminate()

        

    def _save_recording_temp(self):

        """Save recorded audio to WAV file"""

        if not self.audio_frames:

            return None

            

        # Create filename with index and timestamp

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = OUTPUT_DIR / f"phrase_{self.current_index:05d}_{timestamp}.wav"

        

        # Save WAV file

        with wave.open(str(filename), 'wb') as wf:

            wf.setnchannels(CHANNELS)

            wf.setsampwidth(2)  # 16-bit

            wf.setframerate(SAMPLE_RATE)

            wf.writeframes(b''.join(self.audio_frames))

            

        # Save transcript

        transcript_file = filename.with_suffix('.txt')

        with open(transcript_file, 'w', encoding='utf-8') as f:

            f.write(self.phrases[self.current_index])

            

        return filename

        

    def start_recording(self):

        """Start recording"""

        if self.is_recording:

            return

            

        self.is_recording = True

        self.record_thread = threading.Thread(target=self._record_audio)

        self.record_thread.start()

        print("\n   RECORDING... (press SPACE to stop)")

        

    def stop_recording(self):

        """Stop recording and save (but don't advance yet)"""

        if not self.is_recording:

            return False

            

        self.is_recording = False

        self.record_thread.join()

        

        filename = self._save_recording_temp()

        if filename:

            print(f"   Saved: {filename.name}")

            self.last_recording = filename

            self.pending_save = True  # Mark that we have a recording to confirm

            return True

        else:

            print("   No audio recorded")

            self.pending_save = False

            return False

            

    def confirm_recording(self):

        """Confirm the recording and move to next phrase"""

        if self.pending_save:

            self.current_index += 1

            self._save_progress()

            self.pending_save = False

            print("   Confirmed! Moving to next phrase...")

            return True

        return False

            

    def skip_phrase(self):

        """Skip current phrase"""

        self.current_index += 1

        self._save_progress()

        print("  → Skipped")

        

    def listen_last(self):

        """Play back the last recording"""

        print("  [Listening...]")

        sys.stdout.flush()

        

        if not self.last_recording:

            print("   No recording to play (none tracked)")

            return

        if not self.last_recording.exists():

            print(f"   Recording file not found: {self.last_recording}")

            return

            

        print(f"   Playing: {self.last_recording.name}")

        sys.stdout.flush()

        

        try:

            import subprocess

            # Use ffplay (from ffmpeg) for reliable playback - quiet mode

            result = subprocess.run(

                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', str(self.last_recording)],

                capture_output=True,

                timeout=30

            )

            print("   Playback complete")

        except FileNotFoundError:

            # ffplay not found, try Windows Media Player

            try:

                import os

                os.startfile(str(self.last_recording))

                print("   Opened in default player")

            except Exception as e2:

                print(f"   Playback error: {e2}")

        except Exception as e:

            print(f"   Playback error: {e}")

            

    def rerecord(self):

        """Go back and rerecord the previous phrase"""

        if self.current_index == 0:

            print("   No previous recording to redo")

            return

            

        # Delete the last recording if it exists

        if self.last_recording and self.last_recording.exists():

            transcript = self.last_recording.with_suffix('.txt')

            try:

                self.last_recording.unlink()

                if transcript.exists():

                    transcript.unlink()

                print(f"   Deleted: {self.last_recording.name}")

            except Exception as e:

                print(f"  [WARN] Could not delete: {e}")

                

        # Go back one phrase

        self.current_index -= 1

        self._save_progress()

        self.last_recording = None

        print("  ↩ Ready to rerecord")

        

    def display_current_phrase(self):

        """Display the current phrase to record"""

        if self.current_index >= len(self.phrases):

            print("\n" + "=" * 60)

            print("[PARTY] ALL PHRASES RECORDED! Training data complete.")

            print("=" * 60)

            self.running = False

            return

            

        phrase = self.phrases[self.current_index]

        progress = f"{self.current_index + 1}/{len(self.phrases)}"

        percent = (self.current_index / len(self.phrases)) * 100

        

        # Wrap long phrases to fit in terminal (50 chars with indent)

        wrapped = textwrap.fill(phrase, width=50)

        wrapped_lines = '\n     '.join(wrapped.split('\n'))

        

        print("\n" + "=" * 60)

        print(f"  Phrase {progress} ({percent:.1f}%)")

        print("=" * 60)

        print(f"\n  [BOOK] READ THIS:\n")

        print(f"     \"{wrapped_lines}\"\n")

        print("-" * 60)

        if self.pending_save:

            print("  [ENTER] Accept | [l] Listen | [r] Redo | [s] Skip | [q] Quit")

        else:

            print("  [ENTER] Record | [s] Skip | [l] Listen | [q] Quit")

        print("-" * 60)

        

    def run(self):

        """Main recording loop"""

        print("\n" + "=" * 60)

        print("   STT TRAINING RECORDER")

        print("=" * 60)

        print(f"\n  Total phrases: {len(self.phrases)}")

        print(f"  Already recorded: {self.current_index}")

        print(f"  Remaining: {len(self.phrases) - self.current_index}")

        print(f"\n  Output: {OUTPUT_DIR}")

        print("\n  Instructions:")

        print("  1. Press ENTER to start recording")

        print("  2. Read the phrase clearly")

        print("  3. Press ENTER again to stop and save")

        print("  4. Type 's' to skip a phrase")

        print("  5. Type 'l' to listen to last recording")

        print("  6. Type 'r' to redo/rerecord previous phrase")

        print("  7. Type 'q' to quit (progress is saved)")

        print("\n  Press ENTER to begin...")

        

        input()

        

        self.display_current_phrase()

        

        while self.running:

            try:

                cmd = input("  > ").strip().lower()

            except EOFError:

                break

            

            if cmd == '':  # ENTER

                if self.is_recording:

                    # Stop recording (but stay on same phrase)

                    self.stop_recording()

                    print("\n  Now: [ENTER] Accept | [l] Listen | [r] Redo")

                elif self.pending_save:

                    # Confirm and move to next phrase

                    self.confirm_recording()

                    self.display_current_phrase()

                else:

                    # Start recording

                    self.start_recording()

                    

            elif cmd == 's' or cmd == 'skip':  # Skip

                if self.is_recording:

                    print("  [WARN] Stop recording first (press ENTER)")

                else:

                    # If pending save, delete it and skip

                    if self.pending_save and self.last_recording and self.last_recording.exists():

                        self.last_recording.unlink()

                        transcript = self.last_recording.with_suffix('.txt')

                        if transcript.exists():

                            transcript.unlink()

                        print("   Discarded recording")

                    self.pending_save = False

                    self.skip_phrase()

                    self.display_current_phrase()

                    

            elif cmd == 'l' or cmd == 'listen':  # Listen

                if self.is_recording:

                    print("  [WARN] Stop recording first (press ENTER)")

                else:

                    self.listen_last()

                    sys.stdout.flush()

                    

            elif cmd == 'r' or cmd == 'redo':  # Rerecord

                if self.is_recording:

                    print("  [WARN] Stop recording first (press ENTER)")

                else:

                    # Delete current pending recording and re-record same phrase

                    if self.pending_save and self.last_recording and self.last_recording.exists():

                        self.last_recording.unlink()

                        transcript = self.last_recording.with_suffix('.txt')

                        if transcript.exists():

                            transcript.unlink()

                        print("   Deleted recording, ready to redo")

                    self.pending_save = False

                    self.last_recording = None

                    self.display_current_phrase()

                    

            elif cmd == 'q' or cmd == 'quit':  # Quit

                if self.is_recording:

                    self.stop_recording()

                print("\n\nQuitting... Progress saved!")

                print(f"Recorded {self.current_index} phrases so far.")

                self.running = False

                

            else:

                print(f"  [?] Unknown command: '{cmd}'")

                print("     Commands: ENTER=record, s=skip, l=listen, r=redo, q=quit")

                    

        print("\nDone!")





def main():

    if not HAS_PYAUDIO:

        print("\nMissing pyaudio. Install with:")

        print("  pip install pyaudio")

        sys.exit(1)

        

    recorder = STTRecorder()

    recorder.run()





if __name__ == "__main__":

    main()

