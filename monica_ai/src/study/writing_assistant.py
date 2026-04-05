"""
Monica Writing Assistant
Provides Grammarly-level writing assistance with style transfer capabilities.
Can rewrite text in different tones: formal, informal, friendly, professional, etc.

Author: Monica AI
Date: December 2025
"""

import re
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class WritingTone(Enum):
    """Available writing tones/styles."""
    FORMAL = "formal"
    INFORMAL = "informal"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    COMPASSIONATE = "compassionate"
    COOPERATIVE = "cooperative"
    DIPLOMATIC = "diplomatic"
    ASSERTIVE = "assertive"
    PERSUASIVE = "persuasive"
    ACADEMIC = "academic"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    NEUTRAL = "neutral"
    EMPATHETIC = "empathetic"
    CONFIDENT = "confident"


@dataclass
class WritingSuggestion:
    """A writing improvement suggestion."""
    original: str
    suggestion: str
    reason: str
    category: str  # grammar, style, clarity, tone, word_choice


@dataclass
class WritingAnalysis:
    """Analysis of a piece of writing."""
    text: str
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    readability_score: float  # Flesch-Kincaid
    tone: str
    suggestions: List[WritingSuggestion]
    improved_versions: Dict[str, str]  # tone -> rewritten text


class WritingAssistant:
    """
    Provides comprehensive writing assistance including:
    - Grammar and spelling correction
    - Style improvements
    - Tone transformation
    - Clarity enhancements
    - Word choice suggestions
    """
    
    def __init__(self, ai_manager=None):
        self.ai_manager = ai_manager
        
        # Word replacements for different tones
        self.tone_words = self._init_tone_words()
        
        # Common weak words to strengthen
        self.weak_words = {
            'very': ['extremely', 'remarkably', 'exceptionally', 'incredibly'],
            'really': ['truly', 'genuinely', 'absolutely', 'certainly'],
            'good': ['excellent', 'outstanding', 'superb', 'exceptional'],
            'bad': ['poor', 'inadequate', 'substandard', 'unsatisfactory'],
            'nice': ['pleasant', 'delightful', 'wonderful', 'lovely'],
            'big': ['substantial', 'significant', 'considerable', 'immense'],
            'small': ['minor', 'modest', 'slight', 'minimal'],
            'thing': ['matter', 'aspect', 'element', 'factor'],
            'stuff': ['materials', 'items', 'content', 'elements'],
            'got': ['received', 'obtained', 'acquired', 'secured'],
            'get': ['obtain', 'acquire', 'receive', 'secure'],
            'a lot': ['numerous', 'many', 'substantial', 'considerable'],
            'kind of': ['somewhat', 'rather', 'fairly', 'moderately'],
            'sort of': ['somewhat', 'rather', 'to some extent', 'in a way'],
        }
        
        # Formal/informal word pairs
        self.formal_informal = {
            # Informal -> Formal
            'gonna': 'going to',
            'wanna': 'want to',
            'gotta': 'have to',
            'kinda': 'kind of',
            'sorta': 'sort of',
            'dunno': 'do not know',
            'lemme': 'let me',
            'gimme': 'give me',
            'yeah': 'yes',
            'nope': 'no',
            'ok': 'acceptable',
            'okay': 'acceptable',
            'cool': 'acceptable',
            'awesome': 'excellent',
            'stuff': 'materials',
            'things': 'items',
            'kids': 'children',
            'guys': 'people',
            'a lot of': 'numerous',
            'lots of': 'many',
            'pretty much': 'essentially',
            'kind of': 'somewhat',
            'sort of': 'rather',
            'like': '',  # filler word
            'you know': '',  # filler
            'basically': '',  # filler
            'actually': '',  # often unnecessary
            'literally': '',  # often misused
        }
        
        # Phrase improvements
        self.phrase_improvements = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'in the event that': 'if',
            'at this point in time': 'now',
            'in the near future': 'soon',
            'in spite of the fact that': 'although',
            'for the purpose of': 'to',
            'with regard to': 'regarding',
            'in reference to': 'about',
            'it is important to note that': '',
            'it should be noted that': '',
            'needless to say': '',
            'as a matter of fact': '',
            'the fact that': 'that',
            'whether or not': 'whether',
            'each and every': 'every',
            'first and foremost': 'first',
            'any and all': 'all',
            'null and void': 'void',
        }
        
        # Email templates by tone
        self.email_templates = self._init_email_templates()
        
        print("[WRITING] Writing Assistant initialized")
    
    def _init_tone_words(self) -> Dict[str, Dict[str, str]]:
        """Initialize tone-specific word replacements."""
        return {
            WritingTone.FORMAL.value: {
                'hi': 'Dear',
                'hey': 'Dear',
                'thanks': 'Thank you',
                'sorry': 'I apologize',
                'can\'t': 'cannot',
                'won\'t': 'will not',
                'don\'t': 'do not',
                'isn\'t': 'is not',
                'aren\'t': 'are not',
                'i\'m': 'I am',
                'we\'re': 'we are',
                'they\'re': 'they are',
                'let\'s': 'let us',
                'asap': 'at your earliest convenience',
                'fyi': 'for your information',
                'btw': 'additionally',
            },
            WritingTone.FRIENDLY.value: {
                'Dear Sir/Madam': 'Hi there',
                'Dear': 'Hi',
                'Sincerely': 'Best',
                'Regards': 'Cheers',
                'I am writing to': 'I wanted to',
                'Please be advised': 'Just so you know',
                'I would like to': 'I\'d love to',
                'at your earliest convenience': 'when you get a chance',
                'do not hesitate to': 'feel free to',
            },
            WritingTone.COMPASSIONATE.value: {
                'you must': 'you might consider',
                'you should': 'you may want to',
                'you need to': 'it would help to',
                'you have to': 'it\'s important to',
                'wrong': 'could be improved',
                'bad': 'challenging',
                'problem': 'situation',
                'failure': 'setback',
                'mistake': 'learning opportunity',
            },
            WritingTone.DIPLOMATIC.value: {
                'you\'re wrong': 'I see it differently',
                'that\'s incorrect': 'I have a different understanding',
                'I disagree': 'I have a different perspective',
                'no': 'that may not be the best approach',
                'but': 'however',
                'problem': 'challenge',
                'issue': 'matter',
                'complaint': 'concern',
                'demand': 'request',
            },
            WritingTone.PROFESSIONAL.value: {
                'hi': 'Hello',
                'hey': 'Hello',
                'thanks': 'Thank you',
                'gonna': 'going to',
                'wanna': 'want to',
                'yeah': 'yes',
                'nope': 'no',
                'cool': 'excellent',
                'awesome': 'outstanding',
            },
        }
    
    def _init_email_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize email templates for different tones."""
        return {
            WritingTone.FORMAL.value: {
                'greeting': 'Dear {name},',
                'opening': 'I hope this message finds you well.',
                'closing': 'Thank you for your time and consideration.',
                'signature': 'Sincerely,',
            },
            WritingTone.FRIENDLY.value: {
                'greeting': 'Hi {name}!',
                'opening': 'Hope you\'re doing great!',
                'closing': 'Let me know if you have any questions!',
                'signature': 'Best,',
            },
            WritingTone.PROFESSIONAL.value: {
                'greeting': 'Hello {name},',
                'opening': 'I hope this email finds you well.',
                'closing': 'Please let me know if you need any additional information.',
                'signature': 'Best regards,',
            },
            WritingTone.COMPASSIONATE.value: {
                'greeting': 'Dear {name},',
                'opening': 'I hope you\'re taking care of yourself.',
                'closing': 'Please know that I\'m here to support you.',
                'signature': 'With warm regards,',
            },
            WritingTone.DIPLOMATIC.value: {
                'greeting': 'Dear {name},',
                'opening': 'Thank you for reaching out.',
                'closing': 'I appreciate your understanding and cooperation.',
                'signature': 'Respectfully,',
            },
        }
    
    def analyze_writing(self, text: str) -> WritingAnalysis:
        """
        Analyze a piece of writing and provide suggestions.
        """
        # Basic metrics
        words = text.split()
        word_count = len(words)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Readability (simplified Flesch-Kincaid)
        syllables = sum(self._count_syllables(word) for word in words)
        if word_count > 0 and sentence_count > 0:
            readability = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllables / word_count)
            readability = max(0, min(100, readability))
        else:
            readability = 50
        
        # Detect current tone
        tone = self._detect_tone(text)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(text)
        
        # Generate improved versions in different tones
        improved_versions = {}
        for tone_enum in [WritingTone.FORMAL, WritingTone.FRIENDLY, WritingTone.PROFESSIONAL]:
            improved_versions[tone_enum.value] = self.rewrite_in_tone(text, tone_enum.value)
        
        return WritingAnalysis(
            text=text,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            readability_score=readability,
            tone=tone,
            suggestions=suggestions,
            improved_versions=improved_versions
        )
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)."""
        word = word.lower()
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1
        
        return max(1, count)
    
    def _detect_tone(self, text: str) -> str:
        """Detect the current tone of the text."""
        text_lower = text.lower()
        
        # Check for formal indicators
        formal_indicators = ['dear', 'sincerely', 'regards', 'hereby', 'pursuant', 'aforementioned']
        informal_indicators = ['hi', 'hey', 'gonna', 'wanna', 'cool', 'awesome', '!']
        friendly_indicators = ['hope you', 'looking forward', 'great to', 'excited', 'happy to']
        
        formal_count = sum(1 for word in formal_indicators if word in text_lower)
        informal_count = sum(1 for word in informal_indicators if word in text_lower)
        friendly_count = sum(1 for word in friendly_indicators if word in text_lower)
        
        if formal_count > informal_count and formal_count > friendly_count:
            return WritingTone.FORMAL.value
        elif friendly_count > informal_count:
            return WritingTone.FRIENDLY.value
        elif informal_count > 0:
            return WritingTone.INFORMAL.value
        else:
            return WritingTone.NEUTRAL.value
    
    def _generate_suggestions(self, text: str) -> List[WritingSuggestion]:
        """Generate writing improvement suggestions."""
        suggestions = []
        text_lower = text.lower()
        
        # Check for weak words
        for weak, alternatives in self.weak_words.items():
            if weak in text_lower:
                suggestions.append(WritingSuggestion(
                    original=weak,
                    suggestion=alternatives[0],
                    reason=f"'{weak}' is a weak word. Consider using stronger alternatives like: {', '.join(alternatives[:3])}",
                    category='word_choice'
                ))
        
        # Check for wordy phrases
        for wordy, concise in self.phrase_improvements.items():
            if wordy in text_lower:
                if concise:
                    reason_text = f"'{wordy}' is wordy. Use '{concise}' instead."
                else:
                    reason_text = f"'{wordy}' is wordy. Consider removing it."
                suggestions.append(WritingSuggestion(
                    original=wordy,
                    suggestion=concise if concise else '[remove]',
                    reason=reason_text,
                    category='clarity'
                ))
        
        # Check for passive voice (simplified)
        passive_patterns = [
            r'\b(was|were|is|are|been|being)\s+\w+ed\b',
            r'\b(was|were|is|are|been|being)\s+\w+en\b',
        ]
        for pattern in passive_patterns:
            if re.search(pattern, text_lower):
                suggestions.append(WritingSuggestion(
                    original='[passive voice detected]',
                    suggestion='[use active voice]',
                    reason='Passive voice detected. Consider using active voice for more direct writing.',
                    category='style'
                ))
                break
        
        # Check sentence length
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 30:
                suggestions.append(WritingSuggestion(
                    original=sentence[:50] + '...',
                    suggestion='[break into shorter sentences]',
                    reason='This sentence is very long. Consider breaking it into shorter sentences for clarity.',
                    category='clarity'
                ))
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    def rewrite_in_tone(self, text: str, tone: str) -> str:
        """
        Rewrite text in a specific tone.
        
        Args:
            text: Original text
            tone: Target tone (formal, informal, friendly, etc.)
        """
        result = text
        
        # Apply tone-specific word replacements
        if tone in self.tone_words:
            for original, replacement in self.tone_words[tone].items():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(original), re.IGNORECASE)
                result = pattern.sub(replacement, result)
        
        # For formal tone, also apply informal->formal conversions
        if tone == WritingTone.FORMAL.value:
            for informal, formal in self.formal_informal.items():
                if formal:  # Skip empty replacements (fillers)
                    pattern = re.compile(r'\b' + re.escape(informal) + r'\b', re.IGNORECASE)
                    result = pattern.sub(formal, result)
        
        # Use AI for better rewriting if available
        if self.ai_manager and len(text) > 20:
            result = self._ai_rewrite(text, tone)
        
        return result
    
    def _ai_rewrite(self, text: str, tone: str) -> str:
        """Use AI to rewrite text in a specific tone."""
        if not self.ai_manager:
            return text
        
        tone_descriptions = {
            WritingTone.FORMAL.value: "formal and professional, suitable for business correspondence",
            WritingTone.INFORMAL.value: "casual and relaxed, like talking to a friend",
            WritingTone.FRIENDLY.value: "warm, approachable, and personable",
            WritingTone.PROFESSIONAL.value: "polished and business-appropriate",
            WritingTone.COMPASSIONATE.value: "empathetic, understanding, and supportive",
            WritingTone.COOPERATIVE.value: "collaborative and team-oriented",
            WritingTone.DIPLOMATIC.value: "tactful, balanced, and considerate of different perspectives",
            WritingTone.ASSERTIVE.value: "confident and direct without being aggressive",
            WritingTone.PERSUASIVE.value: "convincing and compelling",
            WritingTone.ACADEMIC.value: "scholarly and well-researched",
            WritingTone.ENTHUSIASTIC.value: "energetic and excited",
        }
        
        tone_desc = tone_descriptions.get(tone, "clear and effective")
        
        prompt = f"""Rewrite the following text to be {tone_desc}. 
Keep the same meaning but adjust the tone and word choice.
Only output the rewritten text, nothing else.

Original text:
{text}

Rewritten ({tone}) version:"""
        
        try:
            result = self.ai_manager.get_response(prompt)
            return result.strip()
        except:
            return text
    
    def improve_email(self, text: str, tone: str = 'professional', 
                     recipient_name: str = None) -> str:
        """
        Improve an email with proper structure and tone.
        """
        template = self.email_templates.get(tone, self.email_templates['professional'])
        
        # Add greeting if missing
        if not any(text.lower().startswith(g) for g in ['hi', 'hey', 'hello', 'dear']):
            name = recipient_name or '[Name]'
            greeting = template['greeting'].format(name=name)
            text = f"{greeting}\n\n{text}"
        
        # Add closing if missing
        if not any(c in text.lower() for c in ['regards', 'sincerely', 'best', 'thanks', 'cheers']):
            text = f"{text}\n\n{template['closing']}\n\n{template['signature']}"
        
        # Apply tone transformation
        text = self.rewrite_in_tone(text, tone)
        
        return text
    
    def get_alternative_phrasings(self, text: str, count: int = 3) -> List[str]:
        """
        Generate alternative ways to phrase the same text.
        """
        alternatives = []
        
        # Use AI if available
        if self.ai_manager:
            prompt = f"""Provide {count} different ways to write the following text.
Each version should have the same meaning but different wording.
Number each alternative (1., 2., 3., etc.)

Text: {text}

Alternatives:"""
            
            try:
                result = self.ai_manager.get_response(prompt)
                # Parse numbered alternatives
                lines = result.strip().split('\n')
                for line in lines:
                    line = re.sub(r'^\d+[\.\)]\s*', '', line.strip())
                    if line and len(line) > 10:
                        alternatives.append(line)
            except:
                pass
        
        # Fallback: simple word substitutions
        if not alternatives:
            # Try replacing weak words
            alt = text
            for weak, strongs in self.weak_words.items():
                if weak in alt.lower():
                    alt = re.sub(r'\b' + weak + r'\b', strongs[0], alt, flags=re.IGNORECASE)
                    alternatives.append(alt)
                    if len(alternatives) >= count:
                        break
        
        return alternatives[:count]
    
    def check_and_improve(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive check and improvement of text.
        Returns analysis and multiple improved versions.
        """
        analysis = self.analyze_writing(text)
        
        return {
            'original': text,
            'word_count': analysis.word_count,
            'readability': analysis.readability_score,
            'current_tone': analysis.tone,
            'suggestions': [
                {
                    'original': s.original,
                    'suggestion': s.suggestion,
                    'reason': s.reason,
                    'category': s.category
                }
                for s in analysis.suggestions
            ],
            'versions': {
                'formal': analysis.improved_versions.get('formal', text),
                'friendly': analysis.improved_versions.get('friendly', text),
                'professional': analysis.improved_versions.get('professional', text),
            }
        }
    
    def get_available_tones(self) -> List[str]:
        """Get list of available writing tones."""
        return [tone.value for tone in WritingTone]


# Singleton instance
_assistant = None

def get_writing_assistant(ai_manager=None) -> WritingAssistant:
    """Get or create the writing assistant singleton."""
    global _assistant
    if _assistant is None:
        _assistant = WritingAssistant(ai_manager)
    elif ai_manager:
        _assistant.ai_manager = ai_manager
    return _assistant


# Test
if __name__ == "__main__":
    print("Testing Writing Assistant...")
    
    assistant = get_writing_assistant()
    
    # Test text
    test_text = "Hey, I wanna tell you that the meeting was really good and we got a lot of stuff done. Can you send me the notes asap? Thanks!"
    
    print(f"\nOriginal: {test_text}")
    
    # Analyze
    result = assistant.check_and_improve(test_text)
    
    print(f"\nWord count: {result['word_count']}")
    print(f"Current tone: {result['current_tone']}")
    print(f"Readability: {result['readability']:.1f}")
    
    print("\nSuggestions:")
    for s in result['suggestions'][:3]:
        print(f"  - {s['reason']}")
    
    print(f"\nFormal version: {result['versions']['formal']}")
    print(f"\nFriendly version: {result['versions']['friendly']}")
    
    print("\nWriting Assistant ready!")
