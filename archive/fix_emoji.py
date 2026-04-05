"""
Fix ALL Unicode emoji in ALL .py files across the project.
Replaces emoji on EVERY line (print, logger, string literals, comments, etc.)
to prevent Windows cp1252 encoding crashes.

Scans: src/, tests/, scripts/, root .py files
"""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT = pathlib.Path(r'C:\Monica')

# Match ALL common emoji/symbol Unicode ranges that break cp1252
pat = re.compile(
    r'['
    r'\U0001F000-\U0001FFFF'  # Emoticons, symbols, flags, etc.
    r'\u2600-\u27BF'          # Misc symbols, Dingbats
    r'\u2300-\u23FF'          # Misc technical
    r'\u2B00-\u2BFF'          # Misc symbols and arrows
    r'\uFE00-\uFE0F'          # Variation selectors (invisible but problematic)
    r'\u200D'                  # Zero-width joiner
    r'\u20E3'                  # Combining enclosing keycap
    r'\u3030\u303D'            # Wavy dash, part alternation mark
    r'\U0001FA00-\U0001FAFF'  # Chess, extended-A symbols
    r']'
)

EMOJI_MAP = {
    # Documents & Objects
    '\U0001f4cb': '[LIST]', '\U0001f4d6': '[BOOK]', '\U0001f4da': '[BOOKS]',
    '\U0001f4dd': '[NOTE]', '\U0001f4c4': '[DOC]', '\U0001f4c1': '[FOLDER]',
    '\U0001f4dc': '[SCROLL]', '\U0001f4d3': '[NOTEBOOK]', '\U0001f4d5': '[BOOK]',
    '\U0001f4d7': '[BOOK]', '\U0001f4d8': '[BOOK]', '\U0001f4d9': '[BOOK]',
    '\U0001f4d2': '[LEDGER]', '\U0001f4d4': '[NOTE]', '\U0001f4d1': '[CLIP]',
    '\U0001f4cc': '[PIN]', '\U0001f4ce': '[CLIP]', '\U0001f4be': '[DISK]',
    '\U0001f4bf': '[CD]', '\U0001f4c0': '[DVD]',
    # Tech
    '\U0001f4bb': '[PC]', '\U0001f4f1': '[PHONE]', '\U0001f4f7': '[CAMERA]',
    '\U0001f4f9': '[VIDEO]', '\U0001f4fa': '[TV]', '\U0001f4fb': '[RADIO]',
    '\U0001f4f0': '[NEWS]', '\U0001f50d': '[SEARCH]', '\U0001f527': '[TOOL]',
    '\U0001f512': '[LOCK]', '\U0001f513': '[UNLOCK]', '\U0001f6e1': '[SHIELD]',
    '\U0001f6e0': '[TOOLS]', '\U0001f4e6': '[PKG]',
    # Charts & Stats
    '\U0001f4c8': '[CHART+]', '\U0001f4c9': '[CHART-]', '\U0001f4ca': '[CHART]',
    '\U0001f4af': '[100]', '\U0001f3af': '[TARGET]',
    # Communication
    '\U0001f4ac': '[CHAT]', '\U0001f4ad': '[THOUGHT]', '\U0001f4e2': '[LOUD]',
    '\U0001f4e3': '[MEGA]', '\U0001f4e7': '[EMAIL]', '\U0001f4e8': '[MAIL]',
    '\U0001f4e9': '[MAIL]', '\U0001f4ea': '[MAILBOX]', '\U0001f4eb': '[MAILBOX]',
    # Science & Education
    '\U0001f9e0': '[BRAIN]', '\U0001f9ea': '[TEST]', '\U0001f9ec': '[DNA]',
    '\U0001f393': '[GRAD]', '\U0001f3eb': '[SCHOOL]', '\U0001f4a1': '[IDEA]',
    '\U0001f9ed': '[COMPASS]', '\U0001f9ee': '[ABACUS]', '\U0001f9f0': '[TOOLKIT]',
    # Globes & Nature
    '\U0001f30d': '[GLOBE]', '\U0001f30e': '[GLOBE]', '\U0001f30f': '[GLOBE]',
    # Symbols
    '\U0001f525': '[FIRE]', '\U0001f4a5': '[!]', '\U0001f4ab': '[*]',
    '\U0001f389': '[PARTY]', '\U0001f38a': '[CONFETTI]',
    '\U0001f3c6': '[TROPHY]', '\U0001f3a8': '[ART]', '\U0001f3a5': '[FILM]',
    '\U0001f3b5': '[MUSIC]', '\U0001f3b6': '[MUSIC]', '\U0001f3ae': '[GAME]',
    # Money
    '\U0001f4b0': '[$]', '\U0001f4b5': '[$]', '\U0001f4b8': '[$]',
    # Transport & Misc
    '\U0001f680': '[ROCKET]', '\U0001f6a8': '[ALERT]', '\U0001f6ab': '[NO]',
    '\U0001f6d1': '[STOP]', '\U0001f6a7': '[CONSTR]',
    # Faces & Gestures
    '\U0001f914': '[THINK]', '\U0001f916': '[ROBOT]', '\U0001f929': '[STAR_EYES]',
    '\U0001f937': '[SHRUG]', '\U0001f44d': '[OK]', '\U0001f44e': '[NO]',
    '\U0001f44b': '[WAVE]', '\U0001f44f': '[CLAP]', '\U0001f4aa': '[STRONG]',
    '\U0001f469': '[PERSON]', '\U0001f468': '[PERSON]', '\U0001f3c3': '[RUN]',
    '\U0001f9f9': '[BROOM]',
    # Basic symbols (Misc Symbols / Dingbats)
    '\u2705': '[OK]', '\u274c': '[X]', '\u274e': '[X]',
    '\u26a0': '[WARN]', '\u2728': '[+]', '\u2b50': '[STAR]',
    '\u2764': '[HEART]', '\u2611': '[CHECK]', '\u2610': '[ ]',
    '\u2714': '[OK]', '\u2716': '[X]', '\u2139': '[INFO]',
    '\u23f0': '[ALARM]', '\u23f3': '[TIMER]', '\u2699': '[GEAR]',
    '\u260e': '[PHONE]', '\u2615': '[COFFEE]', '\u2702': '[CUT]',
    '\u270f': '[EDIT]', '\u2712': '[PEN]', '\u2757': '[!]',
    '\u2753': '[?]', '\u2734': '[*]', '\u2733': '[*]', '\u271d': '[+]',
    '\u2b06': '[UP]', '\u2b07': '[DOWN]', '\u27a1': '[->]',
    '\u2b05': '[<-]',
    # Invisible/ZWJ
    '\u200d': '', '\ufe0f': '', '\ufe0e': '',
}


def replace_emoji(text):
    """Replace all emoji with ASCII equivalents."""
    def replacer(m):
        return EMOJI_MAP.get(m.group(0), '')
    return pat.sub(replacer, text)


def scan_and_fix(root_dir, label=""):
    """Scan a directory and fix all .py files."""
    fixed_count = 0
    files_fixed = []

    for py in sorted(root_dir.rglob('*.py')):
        if '__pycache__' in str(py):
            continue
        try:
            content = py.read_text(encoding='utf-8', errors='replace')
            if not pat.search(content):
                continue

            new_content = replace_emoji(content)
            if new_content != content:
                # Count changes
                changes = sum(1 for a, b in zip(content, new_content) if a != b)
                py.write_text(new_content, encoding='utf-8')
                files_fixed.append((str(py.relative_to(PROJECT)), changes))
                fixed_count += changes
        except Exception as e:
            print(f'  ERROR: {py.relative_to(PROJECT)}: {e}')

    return fixed_count, files_fixed


def main():
    print("=" * 60)
    print("MONICA AI - FULL EMOJI REMOVAL")
    print("Removes ALL Unicode emoji from ALL .py files")
    print("=" * 60)

    total_fixed = 0
    all_files = []

    # Scan all relevant directories
    for subdir in ['src', 'tests', 'scripts']:
        d = PROJECT / subdir
        if d.exists():
            count, files = scan_and_fix(d, subdir)
            total_fixed += count
            all_files.extend(files)

    # Also scan root .py files
    for py in PROJECT.glob('*.py'):
        if '__pycache__' in str(py):
            continue
        try:
            content = py.read_text(encoding='utf-8', errors='replace')
            if pat.search(content):
                new_content = replace_emoji(content)
                if new_content != content:
                    changes = sum(1 for a, b in zip(content, new_content) if a != b)
                    py.write_text(new_content, encoding='utf-8')
                    all_files.append((py.name, changes))
                    total_fixed += changes
        except Exception as e:
            print(f'  ERROR: {py.name}: {e}')

    print(f"\nFixed {total_fixed} emoji characters in {len(all_files)} files:")
    for f, n in all_files:
        print(f"  [{n:3d} chars] {f}")

    # Verify: re-scan to confirm no emoji remain
    print("\n--- Verification scan ---")
    remaining = 0
    for subdir in ['src', 'tests', 'scripts']:
        d = PROJECT / subdir
        if not d.exists():
            continue
        for py in d.rglob('*.py'):
            if '__pycache__' in str(py):
                continue
            try:
                content = py.read_text(encoding='utf-8', errors='replace')
                matches = pat.findall(content)
                if matches:
                    remaining += len(matches)
                    print(f"  REMAINING: {py.relative_to(PROJECT)} ({len(matches)} emoji)")
            except Exception:
                pass

    if remaining == 0:
        print("  [OK] No emoji remaining in any .py file!")
    else:
        print(f"  [WARN] {remaining} emoji still remaining")

    print(f"\nDone. {total_fixed} total emoji replaced.")


if __name__ == '__main__':
    main()
