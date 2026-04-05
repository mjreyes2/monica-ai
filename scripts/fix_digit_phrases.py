#!/usr/bin/env python3
"""
Fix Digit Phrases - Remove all phrases with digits from record_voice.py
This prevents training crashes due to digit encoding errors.
"""
import re
from pathlib import Path

# Read the original file
file_path = Path("monica_ai/voice_training/record_voice.py")
print(f"Reading {file_path}...")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the marvin_custom section
start_marker = "        # === MARVIN'S CUSTOM PROMPTS (500) ===\n"
end_marker = "        phrases.extend(marvin_custom)\n"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Could not find marvin_custom section!")
    exit(1)

print(f"Found marvin_custom section at characters {start_idx} to {end_idx}")

# Extract the marvin_custom list
marvin_section = content[start_idx:end_idx]
phrases = re.findall(r'"([^"]+)"', marvin_section)

print(f"Total phrases found: {len(phrases)}")

# Filter out phrases with digits
clean_phrases = [p for p in phrases if not re.search(r'\d', p)]
dirty_phrases = [p for p in phrases if re.search(r'\d', p)]

print(f"Phrases WITH digits (removing): {len(dirty_phrases)}")
print(f"Phrases WITHOUT digits (keeping): {len(clean_phrases)}")

# Create the new marvin_custom section
new_section = "        # === MARVIN'S CUSTOM PROMPTS (CLEANED - NO DIGITS) ===\n"
new_section += "        # Removed all phrases with numbers to prevent training crashes\n"
new_section += f"        # Original: 426 phrases, Cleaned: {len(clean_phrases)} phrases\n"
new_section += "        marvin_custom = [\n"

for phrase in clean_phrases:
    # Properly escape quotes and backslashes
    escaped = phrase.replace('\\', '\\\\').replace('"', '\\"')
    new_section += f'            "{escaped}",\n'

new_section += "        ]\n"

# Replace the section
new_content = content[:start_idx] + new_section + content[end_idx:]

# Backup the original file
backup_path = file_path.with_suffix('.py.backup_digits')
print(f"\nBacking up original to: {backup_path}")
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Write the fixed file
print(f"Writing cleaned file to: {file_path}")
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n" + "="*80)
print("SUCCESS! Phrases with digits have been removed!")
print("="*80)
print(f"\nSummary:")
print(f"  Original phrases: {len(phrases)}")
print(f"  Removed (had digits): {len(dirty_phrases)}")
print(f"  Kept (clean): {len(clean_phrases)}")
print(f"\nBackup saved to: {backup_path}")
print(f"\nYou now have {len(clean_phrases)} safe phrases to record!")
print("\n" + "="*80)

# Show some examples of what was removed
print("\nExamples of REMOVED phrases (had digits):")
for phrase in dirty_phrases[:10]:
    print(f"  [X] {phrase}")

print("\nExamples of KEPT phrases (no digits):")
for phrase in clean_phrases[:10]:
    print(f"  [OK] {phrase}")
