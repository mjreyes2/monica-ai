#!/usr/bin/env python3
"""Analyze voice recordings to identify overfitting issues"""
import os
from pathlib import Path
from collections import Counter
import json

print("=" * 60)
print("ANALYZING VOICE RECORDINGS FOR OVERFITTING")
print("=" * 60)

voice_dir = Path("voice_recordings")
if not voice_dir.exists():
    print("❌ Voice recordings directory not found!")
    exit()

# Get all transcriptions
transcriptions = []
audio_files = list(voice_dir.glob("*.wav")) + list(voice_dir.glob("*.mp3"))

print(f"📁 Found {len(audio_files)} audio files")

for audio_file in audio_files:
    transcription = audio_file.stem.replace('_', ' ').replace('-', ' ').strip()
    if len(transcription) >= 3:
        transcriptions.append(transcription.lower())

print(f"✅ Analyzed {len(transcriptions)} transcriptions")

# Find most common words/phrases
word_counter = Counter()
phrase_counter = Counter()

for transcription in transcriptions:
    words = transcription.split()
    for word in words:
        word_counter[word] += 1
    phrase_counter[transcription] += 1

print("\n🔍 TOP 20 MOST COMMON WORDS:")
for word, count in word_counter.most_common(20):
    print(f"   '{word}': {count} times")

print("\n🔍 TOP 10 MOST COMMON PHRASES:")
for phrase, count in phrase_counter.most_common(10):
    print(f"   '{phrase}': {count} times")

# Check for "you" specifically
you_count = word_counter.get('you', 0)
print(f"\n⚠️  WORD 'YOU' APPEARS: {you_count} times")
print(f"   This is {you_count/len(transcriptions)*100:.1f}% of all recordings")

# Find problematic patterns
single_word_phrases = [p for p in transcriptions if len(p.split()) == 1]
very_short_phrases = [p for p in transcriptions if len(p.split()) <= 2]

print(f"\n📊 STATISTICS:")
print(f"   Single word phrases: {len(single_word_phrases)}")
print(f"   Very short phrases (≤2 words): {len(very_short_phrases)}")
print(f"   Average phrase length: {sum(len(p.split()) for p in transcriptions)/len(transcriptions):.1f} words")

# Suggest improvements
print(f"\n💡 SUGGESTIONS TO PREVENT OVERFITTING:")
if you_count > len(transcriptions) * 0.1:
    print("   ⚠️  Too many instances of 'you' - remove these recordings")

if len(single_word_phrases) > len(transcriptions) * 0.3:
    print("   ⚠️  Too many single-word phrases - remove them")

if len(very_short_phrases) > len(transcriptions) * 0.5:
    print("   ⚠️  Too many short phrases - focus on longer sentences")

print("\n✅ RECOMMENDED APPROACH:")
print("   1. Use only phrases with 3+ words")
print("   2. Remove any phrases containing 'you'")
print("   3. Limit to 500 most diverse phrases")
print("   4. Use conservative training parameters")

# Save clean dataset suggestions
clean_phrases = []
for phrase in transcriptions:
    words = phrase.split()
    if len(words) >= 3 and 'you' not in words:
        clean_phrases.append(phrase)

print(f"\n📝 FOUND {len(clean_phrases)} CLEAN PHRASES FOR TRAINING")

# Save to file for reference
with open("clean_phrases.json", "w") as f:
    json.dump(clean_phrases[:500], f, indent=2)

print(f"💾 Saved top 500 clean phrases to 'clean_phrases.json'")

print("\n" + "=" * 60)
