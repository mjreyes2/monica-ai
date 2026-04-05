#!/usr/bin/env python3
"""
Fix emoji encoding issues in Monica AI codebase
"""
import os
import re
from pathlib import Path

def fix_emojis_in_file(filepath):
    """Replace emojis with ASCII equivalents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Replace common emojis with ASCII
        replacements = {
            '[SEARCH]': '[Search]',
            '[OK]': '[OK]',
            '[WARN]': '[WARNING]',
            '[X]': '[ERROR]',
            '[TARGET]': '[Target]',
            '[CHART]': '[Stats]',
            '': '[Mic]',
            '': '[Audio]',
            '': '[Vision]',
            '[BRAIN]': '[Brain]',
            '[IDEA]': '[Idea]',
            '[ALARM]': '[Time]',
            '[NOTE]': '[Note]',
            '[ROCKET]': '[Launch]',
            '[TOOL]': '[Tool]',
            '[FOLDER]': '[Folder]',
            '[DISK]': '[Save]',
            '': '[Refresh]',
            '[+]': '[Sparkle]',
            '[ART]': '[Art]',
            '[CAMERA]': '[Camera]',
            '': '[Web]',
            '': '[Lock]',
            '[STAR]': '[Star]',
            '[MUSIC]': '[Music]',
        }

        for emoji, replacement in replacements.items():
            content = content.replace(emoji, replacement)

        # Remove any remaining emojis (Unicode ranges for emojis)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "]+", flags=re.UNICODE
        )
        content = emoji_pattern.sub('[*]', content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    monica_ai_path = Path('monica_ai/src')

    if not monica_ai_path.exists():
        print("Error: monica_ai/src directory not found")
        return

    fixed_count = 0

    # Process all Python files
    for py_file in monica_ai_path.rglob('*.py'):
        if fix_emojis_in_file(py_file):
            print(f"Fixed: {py_file}")
            fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()
