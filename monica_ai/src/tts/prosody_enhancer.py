"""
Prosody Enhancer for TTS - Improves rhythm, intonation, and natural speech flow.

This module addresses common TTS issues:
1. Unnatural pauses at sentence starts
2. Monotonic intonation
3. Poor rhythm in complex sentences
4. Missing emphasis on important words

Based on best practices from:
- PL-BERT prosody modeling
- MARS5 rhythm and intonation
- Parler-TTS community techniques
- Professional voice acting guidelines

Integration: Modular design - can be enabled/disabled without affecting core TTS.
"""

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class ProsodyStyle(Enum):
    """Speech prosody styles."""
    NEUTRAL = "neutral"
    CONVERSATIONAL = "conversational"
    EXPRESSIVE = "expressive"
    CALM = "calm"
    ENERGETIC = "energetic"
    PROFESSIONAL = "professional"


@dataclass
class ProsodyMarkers:
    """SSML-like prosody markers for TTS engines that support them."""
    rate: float = 1.0  # Speech rate (0.5 = half speed, 2.0 = double speed)
    pitch: float = 1.0  # Pitch modifier (0.5 = lower, 1.5 = higher)
    volume: float = 1.0  # Volume (0.0 to 1.0)
    emphasis: str = "none"  # none, moderate, strong
    break_time: int = 0  # Pause in milliseconds


class ProsodyEnhancer:
    """
    Enhances text for more natural TTS output.
    
    Features:
    - Removes leading punctuation that causes initial pauses
    - Adds natural breath marks for long sentences
    - Emphasizes question words and important terms
    - Handles parentheticals and asides naturally
    - Improves list intonation
    """
    
    # Words that typically receive emphasis in speech
    EMPHASIS_WORDS = {
        # Question words
        'who', 'what', 'where', 'when', 'why', 'how', 'which',
        # Negatives
        'not', 'never', 'no', 'none', 'nothing', 'nobody',
        # Intensifiers
        'very', 'really', 'extremely', 'absolutely', 'definitely',
        'certainly', 'always', 'completely', 'totally',
        # Contrasts
        'but', 'however', 'although', 'instead', 'rather',
        # Important verbs
        'must', 'should', 'need', 'have to', 'important',
    }
    
    # Sentence starters that often cause TTS issues
    PROBLEMATIC_STARTERS = [
        # Leading punctuation
        ',', ';', ':', '.', '!', '?',
        # Whitespace issues
        '\n', '\r', '\t',
        # Common filler starts
        'um', 'uh', 'er', 'ah',
    ]
    
    # Natural pause points (in order of pause length)
    PAUSE_MARKERS = {
        '.': 'long',      # End of sentence - longer pause
        '!': 'long',
        '?': 'long',
        ';': 'medium',    # Semicolon - medium pause
        ':': 'medium',
        ',': 'short',     # Comma - short pause
        '—': 'short',     # Em dash
        '–': 'short',     # En dash
        '...': 'medium',  # Ellipsis
    }
    
    def __init__(self, style: ProsodyStyle = ProsodyStyle.CONVERSATIONAL):
        """
        Initialize the prosody enhancer.
        
        Args:
            style: The prosody style to apply
        """
        self.style = style
        self._style_params = self._get_style_params(style)
    
    def _get_style_params(self, style: ProsodyStyle) -> Dict:
        """Get parameters for the given style."""
        params = {
            ProsodyStyle.NEUTRAL: {
                'rate': 1.0,
                'pitch_variation': 0.05,
                'pause_multiplier': 1.0,
                'emphasis_strength': 'moderate',
            },
            ProsodyStyle.CONVERSATIONAL: {
                'rate': 1.05,  # Slightly faster
                'pitch_variation': 0.1,
                'pause_multiplier': 0.9,  # Slightly shorter pauses
                'emphasis_strength': 'moderate',
            },
            ProsodyStyle.EXPRESSIVE: {
                'rate': 1.0,
                'pitch_variation': 0.15,
                'pause_multiplier': 1.1,
                'emphasis_strength': 'strong',
            },
            ProsodyStyle.CALM: {
                'rate': 0.95,  # Slightly slower
                'pitch_variation': 0.05,
                'pause_multiplier': 1.2,  # Longer pauses
                'emphasis_strength': 'moderate',
            },
            ProsodyStyle.ENERGETIC: {
                'rate': 1.1,
                'pitch_variation': 0.12,
                'pause_multiplier': 0.8,
                'emphasis_strength': 'strong',
            },
            ProsodyStyle.PROFESSIONAL: {
                'rate': 0.98,
                'pitch_variation': 0.08,
                'pause_multiplier': 1.0,
                'emphasis_strength': 'moderate',
            },
        }
        return params.get(style, params[ProsodyStyle.NEUTRAL])
    
    def enhance(self, text: str) -> str:
        """
        Enhance text for better TTS prosody.
        
        This is the main entry point. It applies all prosody enhancements
        in the correct order.
        
        Args:
            text: Raw text to enhance
            
        Returns:
            Enhanced text with better prosody characteristics
        """
        if not text or not text.strip():
            return text
        
        # 1. Fix sentence start issues (most important for your pause problem)
        text = self._fix_sentence_starts(text)
        
        # 2. Handle parentheticals and asides
        text = self._handle_parentheticals(text)
        
        # 3. Improve list intonation
        text = self._improve_list_intonation(text)
        
        # 4. Add natural breath marks for long sentences
        text = self._add_breath_marks(text)
        
        # 5. Clean up any artifacts
        text = self._final_cleanup(text)
        
        return text
    
    def _fix_sentence_starts(self, text: str) -> str:
        """
        Fix issues that cause unnatural pauses at sentence starts.
        
        This directly addresses the pause-at-start problem by:
        1. Removing leading punctuation
        2. Removing leading whitespace
        3. Ensuring sentences start cleanly
        """
        # Remove leading whitespace and punctuation
        text = text.lstrip()
        
        # Remove leading punctuation that causes pauses
        while text and text[0] in ',.;:!?':
            text = text[1:].lstrip()
        
        # Fix sentences that start with lowercase after period
        # "Hello. world" -> "Hello. World"
        def capitalize_after_period(match):
            return match.group(1) + match.group(2).upper()
        
        text = re.sub(r'([.!?]\s+)([a-z])', capitalize_after_period, text)
        
        # Remove double spaces that can cause pauses
        text = re.sub(r'\s{2,}', ' ', text)
        
        # Fix common patterns that cause initial pauses
        # "...And then" -> "And then"
        text = re.sub(r'^\.{2,}\s*', '', text)
        
        # Remove leading dashes that cause pauses
        text = re.sub(r'^[-–—]+\s*', '', text)
        
        # Fix quotes that might cause issues
        # Ensure opening quotes are followed immediately by text
        text = re.sub(r'(["\'])\s+', r'\1', text)
        
        return text
    
    def _handle_parentheticals(self, text: str) -> str:
        """
        Handle parenthetical expressions for natural speech.
        
        Parentheticals should be spoken with slightly lower pitch
        and faster rate. Since most TTS engines don't support this
        directly, we add subtle cues.
        """
        # Add slight pause before and after parentheticals
        # "(by the way)" -> ", by the way,"
        def process_parenthetical(match):
            content = match.group(1).strip()
            # Don't add commas if content already has them
            if content.startswith(',') or content.endswith(','):
                return f" {content} "
            return f", {content},"
        
        text = re.sub(r'\(([^)]+)\)', process_parenthetical, text)
        
        # Handle em-dash asides similarly
        # "—like this—" -> ", like this,"
        text = re.sub(r'—([^—]+)—', r', \1,', text)
        
        return text
    
    def _improve_list_intonation(self, text: str) -> str:
        """
        Improve intonation for lists.
        
        Lists should have rising intonation on items and falling
        on the last item. We can hint at this with punctuation.
        """
        # Find lists with "and" or "or"
        # "apples, oranges, and bananas" - already good
        # "apples oranges and bananas" -> "apples, oranges, and bananas"
        
        # Add commas before "and" in lists if missing
        # But be careful not to add before "and" in other contexts
        
        # Pattern: word word and word (likely a list)
        def add_list_commas(match):
            items = match.group(0)
            # Only if there are at least 3 items
            words = items.split()
            if len(words) >= 4:  # "a b and c" = 4 words
                # Find "and" or "or" and add comma before
                result = re.sub(r'\s+(and|or)\s+', r', \1 ', items)
                return result
            return items
        
        # Simple list pattern
        text = re.sub(r'\b(\w+\s+){2,}(and|or)\s+\w+\b', add_list_commas, text)
        
        return text
    
    def _add_breath_marks(self, text: str) -> str:
        """
        Add natural breath marks for long sentences.
        
        Long sentences without pauses sound unnatural. This adds
        subtle pause points at natural boundaries.
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        processed = []
        
        for sentence in sentences:
            # If sentence is very long (>100 chars), add breath marks
            if len(sentence) > 100:
                sentence = self._add_breath_to_sentence(sentence)
            processed.append(sentence)
        
        return ' '.join(processed)
    
    def _add_breath_to_sentence(self, sentence: str) -> str:
        """Add breath marks to a long sentence."""
        # Natural breath points (in order of preference):
        # 1. Before conjunctions (and, but, or, so, yet)
        # 2. Before relative pronouns (which, that, who)
        # 3. After prepositional phrases
        
        # Add comma before conjunctions if sentence is long
        # and there isn't already a comma
        conjunctions = ['and', 'but', 'or', 'so', 'yet', 'because', 'although', 'while']
        
        for conj in conjunctions:
            # Pattern: no comma before conjunction
            pattern = rf'(\w)\s+({conj})\s+'
            # Only add if the part before is long enough (>30 chars)
            def maybe_add_comma(match):
                before = sentence[:match.start()]
                if len(before) > 30 and ',' not in before[-15:]:
                    return f'{match.group(1)}, {match.group(2)} '
                return match.group(0)
            
            sentence = re.sub(pattern, maybe_add_comma, sentence, flags=re.IGNORECASE)
        
        return sentence
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup pass."""
        # Remove double commas
        text = re.sub(r',\s*,', ',', text)
        
        # Remove comma before period
        text = re.sub(r',\s*\.', '.', text)
        
        # Ensure single space after punctuation
        text = re.sub(r'([.!?,;:])\s*', r'\1 ', text)
        
        # Remove trailing space before end punctuation
        text = re.sub(r'\s+([.!?])', r'\1', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s{2,}', ' ', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def get_ssml(self, text: str) -> str:
        """
        Convert text to SSML for TTS engines that support it.
        
        SSML (Speech Synthesis Markup Language) provides fine-grained
        control over prosody. Not all TTS engines support this.
        
        Args:
            text: Plain text to convert
            
        Returns:
            SSML-formatted text
        """
        # First enhance the text
        text = self.enhance(text)
        
        # Wrap in SSML
        rate = self._style_params['rate']
        
        ssml = f'<speak>'
        ssml += f'<prosody rate="{rate}">'
        
        # Add emphasis to important words
        for word in self.EMPHASIS_WORDS:
            pattern = rf'\b({word})\b'
            replacement = rf'<emphasis level="moderate">\1</emphasis>'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        ssml += text
        ssml += '</prosody>'
        ssml += '</speak>'
        
        return ssml


class TTSPreprocessor:
    """
    Complete TTS preprocessing pipeline.
    
    Combines text normalization and prosody enhancement into a single
    modular preprocessor that can be easily integrated into any TTS system.
    """
    
    def __init__(
        self,
        enable_normalization: bool = True,
        enable_prosody: bool = True,
        prosody_style: ProsodyStyle = ProsodyStyle.CONVERSATIONAL
    ):
        """
        Initialize the TTS preprocessor.
        
        Args:
            enable_normalization: Whether to normalize text (numbers, dates, etc.)
            enable_prosody: Whether to enhance prosody
            prosody_style: Style for prosody enhancement
        """
        self.enable_normalization = enable_normalization
        self.enable_prosody = enable_prosody
        
        # Lazy load components
        self._normalizer = None
        self._prosody_enhancer = None
        self._prosody_style = prosody_style
    
    @property
    def normalizer(self):
        """Get or create the text normalizer."""
        if self._normalizer is None and self.enable_normalization:
            try:
                from .text_normalizer import TextNormalizer
                self._normalizer = TextNormalizer()
            except ImportError:
                print("[TTS-PREPROCESS] Text normalizer not available")
        return self._normalizer
    
    @property
    def prosody_enhancer(self):
        """Get or create the prosody enhancer."""
        if self._prosody_enhancer is None and self.enable_prosody:
            self._prosody_enhancer = ProsodyEnhancer(style=self._prosody_style)
        return self._prosody_enhancer
    
    def process(self, text: str) -> str:
        """
        Process text through the complete TTS preprocessing pipeline.
        
        Order:
        1. Text normalization (numbers, dates, abbreviations)
        2. Prosody enhancement (rhythm, pauses, emphasis)
        
        Args:
            text: Raw text to process
            
        Returns:
            Processed text ready for TTS
        """
        if not text:
            return text
        
        # Step 1: Normalize text
        if self.normalizer:
            try:
                text = self.normalizer.normalize(text)
            except Exception as e:
                print(f"[TTS-PREPROCESS] Normalization error: {e}")
        
        # Step 2: Enhance prosody
        if self.prosody_enhancer:
            try:
                text = self.prosody_enhancer.enhance(text)
            except Exception as e:
                print(f"[TTS-PREPROCESS] Prosody error: {e}")
        
        return text


# Convenience functions
_preprocessor = None


def get_tts_preprocessor(
    enable_normalization: bool = True,
    enable_prosody: bool = True,
    prosody_style: ProsodyStyle = ProsodyStyle.CONVERSATIONAL
) -> TTSPreprocessor:
    """Get or create the TTS preprocessor."""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = TTSPreprocessor(
            enable_normalization=enable_normalization,
            enable_prosody=enable_prosody,
            prosody_style=prosody_style
        )
    return _preprocessor


def preprocess_for_tts(text: str) -> str:
    """
    Convenience function to preprocess text for TTS.
    
    Args:
        text: Raw text
        
    Returns:
        Processed text ready for TTS
    """
    return get_tts_preprocessor().process(text)


def enhance_prosody(text: str, style: ProsodyStyle = ProsodyStyle.CONVERSATIONAL) -> str:
    """
    Convenience function to enhance prosody only.
    
    Args:
        text: Text to enhance
        style: Prosody style
        
    Returns:
        Enhanced text
    """
    enhancer = ProsodyEnhancer(style=style)
    return enhancer.enhance(text)


# Test function
def test_prosody_enhancer():
    """Test the prosody enhancer with sample texts."""
    enhancer = ProsodyEnhancer()
    
    test_cases = [
        # Leading punctuation (your main issue)
        ", Hello there!",
        "...And then it happened.",
        "  , Well, let me think.",
        
        # Long sentences
        "This is a very long sentence that goes on and on without any natural pause points and it sounds very unnatural when spoken by a TTS system because there are no breaks.",
        
        # Lists
        "I need apples oranges and bananas from the store.",
        
        # Parentheticals
        "The project (which started last year) is almost complete.",
        
        # Normal text (should be unchanged)
        "Hello, how are you today?",
    ]
    
    print("=" * 60)
    print("PROSODY ENHANCER TEST")
    print("=" * 60)
    
    for text in test_cases:
        enhanced = enhancer.enhance(text)
        print(f"\nOriginal: {text}")
        print(f"Enhanced: {enhanced}")
        if text != enhanced:
            print("  [CHANGED]")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_prosody_enhancer()
