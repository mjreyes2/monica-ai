"""
Text Normalizer for TTS - Converts text to natural spoken form.

Enhanced with:
- Custom lexicon for names and acronyms (MJP, Monica, etc.)
- Symbol filtering (removes *, &, etc.)
- Prosody improvements (better punctuation handling)
- Number/date/time conversion

Based on best practices from:
- NVIDIA NeMo TN/ITN pipelines
- Coqui TTS text processing
- OpenAI Whisper prompting guide

Uses lazy loading to avoid slowing down startup - libraries are loaded on first use.
"""

import re
from typing import Optional, Dict

# Lazy loading for heavy libraries
HAS_NUM2WORDS = None  # None = not checked yet
HAS_INFLECT = None
_num2words = None
_inflect_engine = None


def _load_num2words():
    """Lazy load num2words library."""
    global _num2words, HAS_NUM2WORDS
    if HAS_NUM2WORDS is None:
        try:
            import num2words
            _num2words = num2words
            HAS_NUM2WORDS = True
        except ImportError:
            HAS_NUM2WORDS = False
            print("[TTS] num2words not available - using fallback")
    return _num2words if HAS_NUM2WORDS else None


def _load_inflect():
    """Lazy load inflect library."""
    global _inflect_engine, HAS_INFLECT
    if HAS_INFLECT is None:
        try:
            import inflect
            _inflect_engine = inflect.engine()
            HAS_INFLECT = True
        except ImportError:
            HAS_INFLECT = False
            _inflect_engine = None
            print("[TTS] inflect not available - using fallback")
    return _inflect_engine if HAS_INFLECT else None


# For backward compatibility
def get_inflect_engine():
    """Get inflect engine, loading if necessary."""
    return _load_inflect()


def get_num2words():
    """Get num2words module, loading if necessary."""
    return _load_num2words()


class TextNormalizer:
    """
    Normalizes text for natural TTS output.
    
    Converts:
    - Years (2025 -> "twenty twenty-five")
    - Numbers (42 -> "forty-two")
    - Ordinals (1st -> "first")
    - Dates (December 7 -> "December seventh")
    - Times (14:30 -> "two thirty PM")
    - Currency ($5.99 -> "five dollars and ninety-nine cents")
    - Percentages (50% -> "fifty percent")
    - Abbreviations (Dr. -> "Doctor")
    """
    
    # Common abbreviations
    ABBREVIATIONS = {
        'Dr.': 'Doctor',
        'Mr.': 'Mister',
        'Mrs.': 'Missus',
        'Ms.': 'Miss',
        'Prof.': 'Professor',
        'Jr.': 'Junior',
        'Sr.': 'Senior',
        'St.': 'Saint',
        'vs.': 'versus',
        'etc.': 'et cetera',
        'e.g.': 'for example',
        'i.e.': 'that is',
        'Inc.': 'Incorporated',
        'Corp.': 'Corporation',
        'Ltd.': 'Limited',
        'Co.': 'Company',
        'Ave.': 'Avenue',
        'Blvd.': 'Boulevard',
        'Rd.': 'Road',
        'Apt.': 'Apartment',
        'approx.': 'approximately',
        'govt.': 'government',
        'dept.': 'department',
        'min.': 'minutes',
        'sec.': 'seconds',
        'hr.': 'hours',
        'ft.': 'feet',
        'lb.': 'pounds',
        'oz.': 'ounces',
        'mph': 'miles per hour',
        'kph': 'kilometers per hour',
        'km': 'kilometers',
        'cm': 'centimeters',
        'mm': 'millimeters',
        'kg': 'kilograms',
        'mg': 'milligrams',
        'ml': 'milliliters',
        'AI': 'A I',
        'USA': 'U S A',
        'UK': 'U K',
        'EU': 'E U',
        'CEO': 'C E O',
        'CFO': 'C F O',
        'CTO': 'C T O',
        'PhD': 'P H D',
        'MBA': 'M B A',
        'FAQ': 'F A Q',
        'DIY': 'D I Y',
        'ASAP': 'A S A P',
        'FYI': 'F Y I',
        'BTW': 'by the way',
        'IMO': 'in my opinion',
        'TBD': 'to be determined',
        'N/A': 'not applicable',
        'aka': 'also known as',
        'w/': 'with',
        'w/o': 'without',
    }
    
    # Custom lexicon for names and special terms
    # These are spoken exactly as specified (phonetic spelling)
    CUSTOM_LEXICON = {
        # Monica-specific
        'MJP': 'em jay pee',
        'Monica': 'Monica',  # Ensure correct pronunciation
        'Marvin': 'Marvin',
        
        # Tech terms
        'API': 'A P I',
        'GPU': 'G P U',
        'CPU': 'C P U',
        'RAM': 'ram',
        'ROM': 'rom',
        'USB': 'U S B',
        'HDMI': 'H D M I',
        'WiFi': 'why fye',
        'iOS': 'eye O S',
        'macOS': 'mac O S',
        'Linux': 'Linux',
        'Python': 'Python',
        'JavaScript': 'Java Script',
        'HTML': 'H T M L',
        'CSS': 'C S S',
        'SQL': 'sequel',
        'NoSQL': 'no sequel',
        'JSON': 'jay son',
        'XML': 'X M L',
        'HTTP': 'H T T P',
        'HTTPS': 'H T T P S',
        'URL': 'U R L',
        'IP': 'I P',
        'DNS': 'D N S',
        'VPN': 'V P N',
        'SSH': 'S S H',
        'FTP': 'F T P',
        'LLM': 'L L M',
        'GPT': 'G P T',
        'NLP': 'N L P',
        'TTS': 'T T S',
        'STT': 'S T T',
        'ASR': 'A S R',
        'NeMo': 'nee mo',
        'CUDA': 'koo da',
        'PyTorch': 'pie torch',
        'TensorFlow': 'tensor flow',
        'ONNX': 'onyx',
        
        # Common names that might be mispronounced
        'Elon': 'ee lon',
        'Bezos': 'bay zos',
        'Zuckerberg': 'zucker berg',
    }
    
    # Symbols to filter or replace
    SYMBOL_MAP = {
        '*': '',  # Remove asterisks (often used for emphasis in text)
        '**': '',  # Remove double asterisks (markdown bold)
        '***': '',  # Remove triple asterisks
        '~': '',  # Remove tildes
        '`': '',  # Remove backticks
        '```': '',  # Remove code blocks
        '#': 'number ',  # Hash to "number" when followed by digits
        '&': ' and ',  # Ampersand to "and"
        '@': ' at ',  # At sign
        '+': ' plus ',  # Plus sign
        '=': ' equals ',  # Equals sign
        '<': ' less than ',
        '>': ' greater than ',
        '|': '',  # Remove pipes
        '\\': '',  # Remove backslashes
        '_': ' ',  # Underscores to spaces
        '...': ', ',  # Ellipsis to pause
        '—': ', ',  # Em dash to pause
        '–': ', ',  # En dash to pause
        '"': '',  # Remove smart quotes
        '"': '',
        ''': "'",  # Smart apostrophe to regular
        ''': "'",
        '-': '',  # Remove bullet points
        '→': ' to ',  # Arrow
        '←': ' from ',
        '↑': ' up ',
        '↓': ' down ',
    }
    
    # Month names for date parsing
    MONTHS = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    # Ordinal suffixes
    ORDINAL_SUFFIXES = ['st', 'nd', 'rd', 'th']
    
    def __init__(self):
        # Lazy load libraries on first use
        self._inflect = None
        self._num2words = None
        self._libs_loaded = False
    
    def _ensure_libs_loaded(self):
        """Ensure heavy libraries are loaded."""
        if not self._libs_loaded:
            self._inflect = _load_inflect()
            self._num2words = _load_num2words()
            self._libs_loaded = True
    
    @property
    def inflect(self):
        """Get inflect engine, loading if necessary."""
        self._ensure_libs_loaded()
        return self._inflect
    
    @property
    def num2words(self):
        """Get num2words module, loading if necessary."""
        self._ensure_libs_loaded()
        return self._num2words
    
    @property
    def has_num2words(self):
        """Check if num2words is available."""
        self._ensure_libs_loaded()
        return HAS_NUM2WORDS
    
    def normalize(self, text: str) -> str:
        """
        Fully normalize text for TTS.
        
        Processing order (optimized for natural speech):
        1. Filter symbols (remove *, &, etc.)
        2. Apply custom lexicon (MJP -> "em jay pee")
        3. Expand abbreviations (Dr. -> Doctor)
        4. Convert dates and times
        5. Convert numbers and currency
        6. Clean up prosody (punctuation, spacing)
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text ready for TTS
        """
        if not text:
            return text
        
        # Store original for debugging
        original = text
        
        # 0. Filter symbols FIRST (remove markdown, special chars)
        text = self._filter_symbols(text)
        
        # 1. Apply custom lexicon (MJP -> "em jay pee")
        text = self._apply_lexicon(text)
        
        # 2. Expand abbreviations
        text = self._expand_abbreviations(text)
        
        # 3. Convert phone numbers EARLY (before years can match parts of phone numbers)
        # "555-1234" -> "five five five one two three four"
        # "2137112342" -> "two one three seven one one two three four two"
        text = self._convert_phone_numbers(text)

        # 3.5 Repair spaced digits and ordinal suffixes that confuse TTS
        #    e.g., "2 0 2 5" -> "2025", "2 0 t h" -> "20th"
        #    Do this after phone-number conversion to avoid merging digits we already verbalized
        text = self._collapse_spaced_numbers_and_ordinals(text)
        
        # 4. Convert ISO dates and times (YYYY-MM-DD format)
        text = self._convert_iso_datetime(text)
        
        # 5. Convert standalone times (14:30 -> two thirty PM)
        text = self._convert_times(text)
        
        # 6. Convert FULL DATES FIRST (April 20, 1985 -> April twentieth, nineteen eighty-five)
        # This MUST happen before year conversion to handle the year as part of the date
        text = self._convert_dates(text)
        
        # 7. Convert ordinals (1st -> first) - for any remaining ordinals
        text = self._convert_ordinals(text)
        
        # 8. Convert standalone years (2025 -> twenty twenty-five)
        # Only converts years NOT already part of a date
        text = self._convert_years(text)
        
        # 9. Convert currency ($5.99 -> five dollars and ninety-nine cents)
        text = self._convert_currency(text)
        
        # 10. Convert percentages (50% -> fifty percent)
        text = self._convert_percentages(text)
        
        # 11. Convert remaining numbers
        text = self._convert_numbers(text)
        
        # 12. Clean up prosody (fix punctuation spacing for natural pauses)
        text = self._clean_prosody(text)
        
        # 13. Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Debug output (disabled for performance)
        # if text != original:
        #     print(f"[TTS-NORM] '{original[:50]}...' -> '{text[:50]}...'")
        
        return text

    def _collapse_spaced_numbers_and_ordinals(self, text: str) -> str:
        """
        Collapse sequences like "2 0 2 5" -> "2025" and
        spaced ordinal suffixes like "2 0 t h" -> "20th".
        """
        import re
        
        # 1) Join spaced digit sequences (at least two digits with spaces between)
        def join_spaced_digits(m):
            s = m.group(0)
            return re.sub(r"\s+", "", s)
        # Pattern: digit (space digit)+
        text = re.sub(r"\b\d(?:\s+\d){1,}\b", join_spaced_digits, text)
        
        # 2) Join spaced ordinal suffixes after a number: s t | n d | r d | t h
        def join_suffix(m):
            number = m.group(1)
            suffix = re.sub(r"\s+", "", m.group(2))
            return number + suffix
        text = re.sub(r"\b(\d+)\s+(s\s*t|n\s*d|r\s*d|t\s*h)\b", join_suffix, text, flags=re.IGNORECASE)
        
        return text
    
    def _filter_symbols(self, text: str) -> str:
        """
        Filter and replace symbols for natural speech.
        
        Removes markdown formatting, special characters, and converts
        symbols to their spoken equivalents.
        """
        # Handle multi-character symbols first (longer patterns first)
        for symbol in sorted(self.SYMBOL_MAP.keys(), key=len, reverse=True):
            if symbol in text:
                text = text.replace(symbol, self.SYMBOL_MAP[symbol])
        
        # Handle # specially - only convert to "number" when followed by digits
        text = re.sub(r'#(\d)', r'number \1', text)
        # Remove standalone # (like markdown headers)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove any remaining markdown-style formatting
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url) -> text
        
        return text
    
    def _apply_lexicon(self, text: str) -> str:
        """
        Apply custom lexicon for names and special terms.
        
        Converts terms like "MJP" to their phonetic equivalents
        for correct pronunciation.
        """
        for term, pronunciation in self.CUSTOM_LEXICON.items():
            # Use word boundaries to avoid partial matches
            text = re.sub(rf'\b{re.escape(term)}\b', pronunciation, text, flags=re.IGNORECASE)
        
        return text
    
    def _clean_prosody(self, text: str) -> str:
        """
        Clean up punctuation and spacing for natural prosody.
        
        - Removes leading punctuation that causes odd pauses
        - Normalizes spacing around punctuation
        - Ensures natural sentence flow
        """
        # Remove leading commas, periods, or other punctuation that cause initial pauses
        text = re.sub(r'^[\s,;:.!?]+', '', text)
        
        # Remove leading whitespace at start of each sentence (after . ! ?)
        text = re.sub(r'([.!?])\s{2,}', r'\1 ', text)
        
        # Remove multiple consecutive punctuation marks
        text = re.sub(r'[,;:]{2,}', ',', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\?{2,}', '?', text)
        
        # Ensure single space after punctuation
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
        
        # Remove space before punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Remove trailing punctuation followed by more punctuation
        text = re.sub(r'([.,!?])\s*([.,!?])', r'\1', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove empty parentheses
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r'\[\s*\]', '', text)
        
        return text
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations."""
        for abbr, expansion in self.ABBREVIATIONS.items():
            # Use word boundaries for most abbreviations
            if abbr.endswith('.'):
                text = text.replace(abbr, expansion)
            else:
                text = re.sub(rf'\b{re.escape(abbr)}\b', expansion, text)
        return text
    
    def _convert_years(self, text: str) -> str:
        """Convert years to spoken form using num2words."""
        # First: Fix spaced years like "202 5" -> "2025" before processing
        text = re.sub(r'\b(20)(\d)\s+(\d)\b', r'\1\2\3', text)  # "202 5" -> "2025"
        text = re.sub(r'\b(20)\s+(\d{2})\b', r'\1\2', text)     # "20 25" -> "2025"
        text = re.sub(r'\b(19)(\d)\s+(\d)\b', r'\1\2\3', text)  # "199 0" -> "1990"
        text = re.sub(r'\b(19)\s+(\d{2})\b', r'\1\2', text)     # "19 90" -> "1990"
        
        def replace_year(match):
            year_str = match.group(0)
            year = int(year_str)
            
            # Only convert 4-digit years in reasonable range
            if 1000 <= year <= 2099:
                if self.has_num2words and self.num2words:
                    try:
                        # Use 'year' mode for proper year pronunciation
                        # This converts 1990 -> "nineteen ninety" not "one nine nine zero"
                        spoken = self.num2words.num2words(year, to='year')
                        # FIX: Replace spaces with hyphens to prevent Piper from pausing
                        # "twenty twenty-five" -> "twenty-twenty-five"
                        spoken = spoken.replace(' ', '-')
                        return spoken
                    except:
                        pass
                
                # Fallback for years (ensures proper pronunciation)
                return self._year_to_words_fallback(year)
            
            return year_str
        
        # Match 4-digit years (1000-2099) with word boundaries
        # This prevents matching parts of longer numbers
        text = re.sub(r'\b(1[0-9]{3}|20[0-9]{2})\b', replace_year, text)
        
        return text
    
    def _year_to_words_fallback(self, year: int) -> str:
        """Fallback year conversion without num2words - ensures proper year pronunciation."""
        if 2000 <= year <= 2009:
            ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
            if year == 2000:
                return 'two thousand'
            return f'two thousand {ones[year - 2000]}'
        
        if 2010 <= year <= 2099:
            # 2010-2099: "twenty ten", "twenty twenty-five", etc.
            # Use hyphen to prevent Piper from pausing between words
            second = year - 2000
            if second < 10:
                ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
                return f'twenty-{ones[second]}' if second > 0 else 'twenty'
            second_words = self._two_digit_to_words(second)
            # Connect with hyphen to prevent pause: "twenty-twenty-five"
            return f'twenty-{second_words}'
        
        if 1000 <= year <= 1999:
            # 1000-1999: "nineteen ninety", "eighteen fifty", etc.
            first = year // 100
            second = year % 100
            first_word = self._two_digit_to_words(first)
            second_word = self._two_digit_to_words(second)
            if second_word:
                return f'{first_word} {second_word}'
            return first_word
        
        return str(year)
    
    def _two_digit_to_words(self, num: int) -> str:
        """Convert a two-digit number to words."""
        if num == 0:
            return ''
        
        ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
                'seventeen', 'eighteen', 'nineteen']
        tens = ['', 'ten', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
        
        if num < 20:
            return ones[num]
        
        ten = num // 10
        unit = num % 10
        if unit == 0:
            return tens[ten]
        return f'{tens[ten]}-{ones[unit]}'
    
    def _convert_phone_numbers(self, text: str) -> str:
        """
        Convert phone numbers to spoken digits (Retell AI style).
        
        Examples:
        - "2137112342" -> "two one three seven one one two three four two"
        - "555-1234" -> "five five five one two three four"
        - "(555) 123-4567" -> "five five five one two three four five six seven"
        """
        digit_words = {
            '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
            '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
        }
        
        def replace_phone(match):
            phone = match.group(0)
            # Extract just the digits
            digits = re.sub(r'[^\d]', '', phone)
            # Convert each digit to word
            words = ' '.join(digit_words.get(d, d) for d in digits)
            return words
        
        # Match phone number patterns:
        # - 10+ digit numbers (likely phone numbers)
        # - Numbers with dashes/dots/spaces (555-123-4567, 555.123.4567)
        # - Numbers with parentheses ((555) 123-4567)
        
        # Pattern for 10-digit phone numbers (with optional formatting)
        text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', replace_phone, text)
        
        # Pattern for 7-digit phone numbers (555-1234 or 555.1234)
        text = re.sub(r'\b\d{3}[-.\s]\d{4}\b', replace_phone, text)
        
        # Pattern for long digit sequences (7+ digits, likely phone/ID)
        text = re.sub(r'\b\d{7,}\b', replace_phone, text)
        
        return text
    
    def _convert_numbers(self, text: str) -> str:
        """Convert standalone numbers to words."""
        def replace_number(match):
            num_str = match.group(0)
            
            # Skip if it looks like part of a larger pattern (already converted)
            if any(c.isalpha() for c in num_str):
                return num_str
            
            try:
                num = int(num_str)
                
                # Only convert reasonable numbers (not phone numbers, IDs, etc.)
                # Phone numbers are handled separately
                if 0 <= num <= 9999:
                    if self.has_num2words and self.num2words:
                        return self.num2words.num2words(num)
                    elif self.inflect:
                        return self.inflect.number_to_words(num)
            except ValueError:
                pass
            
            return num_str
        
        # Match standalone numbers (not part of dates, times, etc.)
        return re.sub(r'\b\d{1,4}\b', replace_number, text)
    
    def _convert_ordinals(self, text: str) -> str:
        """Convert ordinal numbers (1st, 2nd, 3rd, etc.)."""
        def replace_ordinal(match):
            num = int(match.group(1))
            suffix = match.group(2).lower()
            
            if self.has_num2words and self.num2words:
                try:
                    return self.num2words.num2words(num, to='ordinal')
                except:
                    pass
            
            if self.inflect:
                return self.inflect.ordinal(num)
            
            # Fallback
            ordinals = {
                1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
                6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
                11: 'eleventh', 12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth',
                15: 'fifteenth', 16: 'sixteenth', 17: 'seventeenth', 18: 'eighteenth',
                19: 'nineteenth', 20: 'twentieth', 21: 'twenty-first', 22: 'twenty-second',
                23: 'twenty-third', 24: 'twenty-fourth', 25: 'twenty-fifth',
                26: 'twenty-sixth', 27: 'twenty-seventh', 28: 'twenty-eighth',
                29: 'twenty-ninth', 30: 'thirtieth', 31: 'thirty-first'
            }
            return ordinals.get(num, f'{num}th')
        
        return re.sub(r'\b(\d+)(st|nd|rd|th)\b', replace_ordinal, text, flags=re.IGNORECASE)
    
    def _convert_dates(self, text: str) -> str:
        """Convert date formats to spoken form."""
        
        # Ordinals lookup for days
        ordinals = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
            11: 'eleventh', 12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth',
            15: 'fifteenth', 16: 'sixteenth', 17: 'seventeenth', 18: 'eighteenth',
            19: 'nineteenth', 20: 'twentieth', 21: 'twenty-first', 22: 'twenty-second',
            23: 'twenty-third', 24: 'twenty-fourth', 25: 'twenty-fifth',
            26: 'twenty-sixth', 27: 'twenty-seventh', 28: 'twenty-eighth',
            29: 'twenty-ninth', 30: 'thirtieth', 31: 'thirty-first'
        }
        
        def day_to_ordinal(day: int) -> str:
            if self.has_num2words and self.num2words:
                try:
                    return self.num2words.num2words(day, to='ordinal')
                except:
                    pass
            return ordinals.get(day, str(day))
        
        def year_to_spoken(year: int) -> str:
            if self.has_num2words and self.num2words:
                try:
                    return self.num2words.num2words(year, to='year')
                except:
                    pass
            return self._year_to_words_fallback(year)
        
        # Pattern 1: "April 20, 1985" or "April 20 1985" (Month Day, Year)
        for month in self.MONTHS:
            # With comma: "April 20, 1985"
            pattern = rf'\b{month}\s+(\d{{1,2}}),?\s+(1[89]\d{{2}}|20\d{{2}})\b'
            
            def replace_full_date(match, m=month):
                day = int(match.group(1))
                year = int(match.group(2))
                if 1 <= day <= 31:
                    day_word = day_to_ordinal(day)
                    year_word = year_to_spoken(year)
                    result = f'{m} {day_word}, {year_word}'
                    return result
                return match.group(0)
            
            text = re.sub(pattern, replace_full_date, text)
        
        # Pattern 2: "April 20th, 1985" (already has ordinal suffix)
        for month in self.MONTHS:
            pattern = rf'\b{month}\s+(\d{{1,2}})(st|nd|rd|th),?\s+(1[89]\d{{2}}|20\d{{2}})\b'
            
            def replace_ordinal_date(match, m=month):
                day = int(match.group(1))
                year = int(match.group(3))
                if 1 <= day <= 31:
                    day_word = day_to_ordinal(day)
                    year_word = year_to_spoken(year)
                    result = f'{m} {day_word}, {year_word}'
                    return result
                return match.group(0)
            
            text = re.sub(pattern, replace_ordinal_date, text, flags=re.IGNORECASE)
        
        # Pattern 3: "April 20" without year (Month Day)
        for month in self.MONTHS:
            pattern = rf'\b{month}\s+(\d{{1,2}})\b(?!\s*,?\s*\d{{4}})'
            
            def replace_date(match, m=month):
                day = int(match.group(1))
                if 1 <= day <= 31:
                    day_word = day_to_ordinal(day)
                    return f'{m} {day_word}'
                return match.group(0)
            
            text = re.sub(pattern, replace_date, text)
        
        # Pattern 4: "20th of April, 1985" (Day of Month, Year)
        for month in self.MONTHS:
            pattern = rf'\b(\d{{1,2}})(st|nd|rd|th)?\s+of\s+{month},?\s+(1[89]\d{{2}}|20\d{{2}})\b'
            
            def replace_of_date(match, m=month):
                day = int(match.group(1))
                year = int(match.group(3))
                if 1 <= day <= 31:
                    day_word = day_to_ordinal(day)
                    year_word = year_to_spoken(year)
                    result = f'{day_word} of {m}, {year_word}'
                    print(f"[TTS-NORM] Date (of): {match.group(0)} -> {result}")
                    return result
                return match.group(0)
            
            text = re.sub(pattern, replace_of_date, text, flags=re.IGNORECASE)
        
        # Pattern 5: "the 20th of April" (the Day of Month)
        for month in self.MONTHS:
            pattern = rf'\bthe\s+(\d{{1,2}})(st|nd|rd|th)?\s+of\s+{month}\b'
            
            def replace_the_of_date(match, m=month):
                day = int(match.group(1))
                if 1 <= day <= 31:
                    day_word = day_to_ordinal(day)
                    return f'the {day_word} of {m}'
                return match.group(0)
            
            text = re.sub(pattern, replace_the_of_date, text, flags=re.IGNORECASE)
        
        return text
    
    def _convert_iso_datetime(self, text: str) -> str:
        """Convert ISO datetime format (2025-12-07 14:30)."""
        def replace_datetime(match):
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            
            # Convert components
            month_name = self.MONTHS[month - 1] if 1 <= month <= 12 else str(month)
            
            if self.has_num2words and self.num2words:
                try:
                    day_word = self.num2words.num2words(day, to='ordinal')
                    year_word = self.num2words.num2words(year, to='year')
                except:
                    day_word = str(day)
                    year_word = str(year)
            else:
                day_word = str(day)
                year_word = self._year_to_words_fallback(year)
            
            time_word = self._time_to_words(hour, minute)
            
            return f'{month_name} {day_word}, {year_word} at {time_word}'
        
        # Match YYYY-MM-DD HH:MM or YYYY-MM-DDTHH:MM
        pattern = r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})[ T](\d{1,2}):(\d{2})\b'
        text = re.sub(pattern, replace_datetime, text)
        
        # Also handle date-only format
        def replace_date_only(match):
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            
            month_name = self.MONTHS[month - 1] if 1 <= month <= 12 else str(month)
            
            if self.has_num2words and self.num2words:
                try:
                    day_word = self.num2words.num2words(day, to='ordinal')
                    year_word = self.num2words.num2words(year, to='year')
                except:
                    day_word = str(day)
                    year_word = str(year)
            else:
                day_word = str(day)
                year_word = self._year_to_words_fallback(year)
            
            return f'{month_name} {day_word}, {year_word}'
        
        pattern = r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b'
        text = re.sub(pattern, replace_date_only, text)
        
        return text
    
    def _convert_times(self, text: str) -> str:
        """Convert time format (14:30 -> two thirty PM)."""
        def replace_time(match):
            hour = int(match.group(1))
            minute = int(match.group(2))
            return self._time_to_words(hour, minute)
        
        return re.sub(r'\b([01]?\d|2[0-3]):([0-5]\d)\b', replace_time, text)
    
    def _time_to_words(self, hour: int, minute: int) -> str:
        """Convert hour and minute to spoken form."""
        # Determine AM/PM
        am_pm = 'AM' if hour < 12 else 'PM'
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        
        # Convert hour
        if self.has_num2words and self.num2words:
            try:
                hour_word = self.num2words.num2words(hour_12)
            except:
                hour_word = str(hour_12)
        else:
            hour_word = str(hour_12)
        
        # Convert minute
        if minute == 0:
            return f'{hour_word} {am_pm}'
        elif minute < 10:
            if self.has_num2words and self.num2words:
                try:
                    minute_word = 'oh ' + self.num2words.num2words(minute)
                except:
                    minute_word = f'oh {minute}'
            else:
                minute_word = f'oh {minute}'
        else:
            if self.has_num2words and self.num2words:
                try:
                    minute_word = self.num2words.num2words(minute)
                except:
                    minute_word = str(minute)
            else:
                minute_word = str(minute)
        
        return f'{hour_word} {minute_word} {am_pm}'
    
    def _convert_currency(self, text: str) -> str:
        """Convert currency amounts."""
        def replace_currency(match):
            dollars = int(match.group(1))
            cents = int(match.group(2)) if match.group(2) else 0
            
            if self.has_num2words and self.num2words:
                try:
                    dollar_word = self.num2words.num2words(dollars)
                    if cents > 0:
                        cent_word = self.num2words.num2words(cents)
                        return f'{dollar_word} dollars and {cent_word} cents'
                    return f'{dollar_word} dollars'
                except:
                    pass
            
            if cents > 0:
                return f'{dollars} dollars and {cents} cents'
            return f'{dollars} dollars'
        
        # Match $X.XX or $X
        text = re.sub(r'\$(\d+)(?:\.(\d{2}))?', replace_currency, text)
        return text
    
    def _convert_percentages(self, text: str) -> str:
        """Convert percentages."""
        def replace_percent(match):
            num = match.group(1)
            try:
                n = float(num)
                if n == int(n):
                    n = int(n)
                    if self.has_num2words and self.num2words:
                        return f'{self.num2words.num2words(n)} percent'
                    return f'{n} percent'
                else:
                    # Handle decimal percentages
                    return f'{num} percent'
            except:
                return f'{num} percent'
        
        return re.sub(r'(\d+(?:\.\d+)?)\s*%', replace_percent, text)


# Global instance
_normalizer = None

def get_text_normalizer() -> TextNormalizer:
    """Get the global TextNormalizer instance."""
    global _normalizer
    if _normalizer is None:
        _normalizer = TextNormalizer()
    return _normalizer


def normalize_text_for_tts(text: str) -> str:
    """Convenience function to normalize text for TTS."""
    return get_text_normalizer().normalize(text)
