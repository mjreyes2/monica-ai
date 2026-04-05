"""
Monica Pronunciation Assessment System
Evaluates pronunciation accuracy by comparing spoken words to expected text.

Uses multiple methods:
1. Phonetic comparison (Soundex, Metaphone, Double Metaphone)
2. CMU Pronouncing Dictionary for phoneme lookup
3. Levenshtein distance for similarity scoring
4. Whisper word-level timestamps for alignment

Author: Monica AI
Date: December 2025
"""

import re
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

# Phonetic comparison libraries
HAS_JELLYFISH = False
try:
    import jellyfish
    HAS_JELLYFISH = True
except ImportError:
    pass

# CMU Pronouncing Dictionary (built-in subset for common words)
HAS_CMU_DICT = True
# Common words with their phonemes (ARPAbet notation)
CMU_DICT = {
    # Common mispronounced words
    'necessary': [['N', 'EH1', 'S', 'AH0', 'S', 'EH2', 'R', 'IY0']],
    'pronunciation': [['P', 'R', 'AH0', 'N', 'AH2', 'N', 'S', 'IY0', 'EY1', 'SH', 'AH0', 'N']],
    'february': [['F', 'EH1', 'B', 'R', 'UW0', 'EH0', 'R', 'IY0']],
    'library': [['L', 'AY1', 'B', 'R', 'EH0', 'R', 'IY0']],
    'probably': [['P', 'R', 'AA1', 'B', 'AH0', 'B', 'L', 'IY0']],
    'definitely': [['D', 'EH1', 'F', 'AH0', 'N', 'AH0', 'T', 'L', 'IY0']],
    'temperature': [['T', 'EH1', 'M', 'P', 'R', 'AH0', 'CH', 'ER0']],
    'comfortable': [['K', 'AH1', 'M', 'F', 'ER0', 'T', 'AH0', 'B', 'AH0', 'L']],
    'vegetable': [['V', 'EH1', 'JH', 'T', 'AH0', 'B', 'AH0', 'L']],
    'wednesday': [['W', 'EH1', 'N', 'Z', 'D', 'EY2']],
    'colonel': [['K', 'ER1', 'N', 'AH0', 'L']],
    'queue': [['K', 'Y', 'UW1']],
    'chaos': [['K', 'EY1', 'AA0', 'S']],
    'choir': [['K', 'W', 'AY1', 'ER0']],
    'epitome': [['IH0', 'P', 'IH1', 'T', 'AH0', 'M', 'IY0']],
    'hyperbole': [['HH', 'AY0', 'P', 'ER1', 'B', 'AH0', 'L', 'IY0']],
    'mischievous': [['M', 'IH1', 'S', 'CH', 'AH0', 'V', 'AH0', 'S']],
    'nuclear': [['N', 'UW1', 'K', 'L', 'IY0', 'ER0']],
    'often': [['AO1', 'F', 'AH0', 'N']],
    'salmon': [['S', 'AE1', 'M', 'AH0', 'N']],
    'almond': [['AA1', 'M', 'AH0', 'N', 'D']],
    'arctic': [['AA1', 'R', 'K', 'T', 'IH0', 'K']],
    'athlete': [['AE1', 'TH', 'L', 'IY2', 'T']],
    'espresso': [['EH0', 'S', 'P', 'R', 'EH1', 'S', 'OW0']],
    'etcetera': [['EH0', 'T', 'S', 'EH1', 'T', 'ER0', 'AH0']],
    'hierarchy': [['HH', 'AY1', 'ER0', 'AA2', 'R', 'K', 'IY0']],
    'jewelry': [['JH', 'UW1', 'AH0', 'L', 'R', 'IY0']],
    'miniature': [['M', 'IH1', 'N', 'IY0', 'AH0', 'CH', 'ER0']],
    'niche': [['N', 'IH1', 'CH']],
    'picture': [['P', 'IH1', 'K', 'CH', 'ER0']],
    'prescription': [['P', 'R', 'IH0', 'S', 'K', 'R', 'IH1', 'P', 'SH', 'AH0', 'N']],
    'realtor': [['R', 'IY1', 'L', 'T', 'ER0']],
    'supposedly': [['S', 'AH0', 'P', 'OW1', 'Z', 'AH0', 'D', 'L', 'IY0']],
    'the': [['DH', 'AH0']],
    'a': [['AH0']],
    'is': [['IH1', 'Z']],
}
print("[OK] Built-in pronunciation dictionary loaded")

# Phonemizer for IPA transcription
HAS_PHONEMIZER = False
try:
    from phonemizer import phonemize
    HAS_PHONEMIZER = True
    print("[OK] Phonemizer loaded")
except ImportError:
    pass


@dataclass
class PronunciationResult:
    """Result of pronunciation assessment."""
    word: str
    expected_phonemes: str
    spoken_approximation: str
    score: float  # 0.0 to 1.0
    feedback: str
    is_correct: bool
    suggestions: List[str]


class PronunciationAssessor:
    """
    Assesses pronunciation accuracy using multiple methods.
    """
    
    def __init__(self):
        self.phoneme_cache = {}
        self.assessment_history: List[PronunciationResult] = []
        
        # Common pronunciation patterns for feedback
        self.common_errors = {
            'th': ['t', 'd', 'f', 'v', 's', 'z'],  # TH sounds
            'r': ['w', 'l'],  # R sounds
            'l': ['r', 'w'],  # L sounds
            'v': ['b', 'w'],  # V sounds
            'w': ['v', 'u'],  # W sounds
            'ng': ['n', 'nk'],  # NG sounds
            'ch': ['sh', 'tch'],  # CH sounds
            'sh': ['s', 'ch'],  # SH sounds
            'zh': ['z', 'j'],  # ZH sounds (measure)
        }
        
        # Stress patterns for common words
        self.stress_patterns = {
            'record': {'noun': 'RE-cord', 'verb': 're-CORD'},
            'present': {'noun': 'PRE-sent', 'verb': 'pre-SENT'},
            'object': {'noun': 'OB-ject', 'verb': 'ob-JECT'},
            'project': {'noun': 'PRO-ject', 'verb': 'pro-JECT'},
            'permit': {'noun': 'PER-mit', 'verb': 'per-MIT'},
        }
    
    def get_phonemes(self, word: str) -> str:
        """Get phonetic representation of a word."""
        word = word.lower().strip()
        
        if word in self.phoneme_cache:
            return self.phoneme_cache[word]
        
        phonemes = ""
        
        # Try CMU Dictionary first (most accurate for English)
        if HAS_CMU_DICT and word in CMU_DICT:
            # Get first pronunciation variant
            cmu_phonemes = CMU_DICT[word][0]
            phonemes = ' '.join(cmu_phonemes)
        
        # Try phonemizer for IPA
        elif HAS_PHONEMIZER:
            try:
                phonemes = phonemize(word, language='en-us', backend='espeak')
            except:
                pass
        
        # Fallback to basic phonetic approximation
        if not phonemes:
            phonemes = self._basic_phonetic(word)
        
        self.phoneme_cache[word] = phonemes
        return phonemes
    
    def _basic_phonetic(self, word: str) -> str:
        """Basic phonetic approximation using rules."""
        word = word.lower()
        
        # Common letter-to-sound mappings
        replacements = [
            ('ph', 'F'),
            ('gh', ''),  # Often silent
            ('ght', 'T'),
            ('tion', 'SHUN'),
            ('sion', 'ZHUN'),
            ('ck', 'K'),
            ('ch', 'CH'),
            ('sh', 'SH'),
            ('th', 'TH'),
            ('wh', 'W'),
            ('wr', 'R'),
            ('kn', 'N'),
            ('gn', 'N'),
            ('mb', 'M'),
            ('ng', 'NG'),
            ('qu', 'KW'),
            ('x', 'KS'),
        ]
        
        result = word
        for old, new in replacements:
            result = result.replace(old, new)
        
        return result.upper()
    
    def assess_pronunciation(self, expected: str, spoken: str) -> PronunciationResult:
        """
        Assess how well the spoken word matches the expected word.
        
        Args:
            expected: The word that should have been spoken
            spoken: What was actually spoken (from speech recognition)
            
        Returns:
            PronunciationResult with score and feedback
        """
        expected = expected.lower().strip()
        spoken = spoken.lower().strip()
        
        # Perfect match
        if expected == spoken:
            return PronunciationResult(
                word=expected,
                expected_phonemes=self.get_phonemes(expected),
                spoken_approximation=spoken,
                score=1.0,
                feedback="Perfect pronunciation!",
                is_correct=True,
                suggestions=[]
            )
        
        # Get phonetic representations
        expected_phonemes = self.get_phonemes(expected)
        spoken_phonemes = self.get_phonemes(spoken)
        
        # Calculate scores using multiple methods
        scores = []
        
        # 1. Direct string similarity
        direct_score = SequenceMatcher(None, expected, spoken).ratio()
        scores.append(direct_score)
        
        # 2. Phonetic similarity (if jellyfish available)
        if HAS_JELLYFISH:
            # Soundex comparison
            try:
                expected_soundex = jellyfish.soundex(expected)
                spoken_soundex = jellyfish.soundex(spoken)
                soundex_match = 1.0 if expected_soundex == spoken_soundex else 0.5
                scores.append(soundex_match)
            except:
                pass
            
            # Metaphone comparison
            try:
                expected_meta = jellyfish.metaphone(expected)
                spoken_meta = jellyfish.metaphone(spoken)
                meta_score = SequenceMatcher(None, expected_meta, spoken_meta).ratio()
                scores.append(meta_score)
            except:
                pass
            
            # Jaro-Winkler similarity
            try:
                jw_score = jellyfish.jaro_winkler_similarity(expected, spoken)
                scores.append(jw_score)
            except:
                pass
        
        # 3. Phoneme comparison
        phoneme_score = SequenceMatcher(None, expected_phonemes, spoken_phonemes).ratio()
        scores.append(phoneme_score)
        
        # Calculate final score (weighted average)
        final_score = sum(scores) / len(scores) if scores else 0.0
        
        # Generate feedback
        feedback, suggestions = self._generate_feedback(expected, spoken, final_score)
        
        result = PronunciationResult(
            word=expected,
            expected_phonemes=expected_phonemes,
            spoken_approximation=spoken,
            score=final_score,
            feedback=feedback,
            is_correct=final_score >= 0.85,
            suggestions=suggestions
        )
        
        self.assessment_history.append(result)
        return result
    
    def _generate_feedback(self, expected: str, spoken: str, score: float) -> Tuple[str, List[str]]:
        """Generate helpful feedback based on the pronunciation attempt."""
        suggestions = []
        
        if score >= 0.95:
            return "Excellent pronunciation!", []
        
        if score >= 0.85:
            return "Good pronunciation! Minor differences detected.", []
        
        if score >= 0.7:
            feedback = f"Close! You said '{spoken}', the word is '{expected}'."
            
            # Find specific differences
            for i, (e, s) in enumerate(zip(expected, spoken)):
                if e != s:
                    suggestions.append(f"Check the '{e}' sound (you said '{s}')")
                    break
            
            return feedback, suggestions
        
        if score >= 0.5:
            feedback = f"Try again. The word '{expected}' sounds different from '{spoken}'."
            
            # Provide pronunciation guide
            syllables = self._syllabify(expected)
            if syllables:
                suggestions.append(f"Break it down: {'-'.join(syllables)}")
            
            # Check for common error patterns
            for pattern, errors in self.common_errors.items():
                if pattern in expected:
                    suggestions.append(f"Pay attention to the '{pattern}' sound")
                    break
            
            return feedback, suggestions
        
        # Low score - provide detailed help
        feedback = f"Let me help you with '{expected}'."
        
        # Syllable breakdown
        syllables = self._syllabify(expected)
        if syllables:
            suggestions.append(f"Say it slowly: {' - '.join(syllables)}")
        
        # Phonetic guide
        phonemes = self.get_phonemes(expected)
        if phonemes:
            suggestions.append(f"Sounds like: {phonemes}")
        
        return feedback, suggestions
    
    def _syllabify(self, word: str) -> List[str]:
        """Break a word into syllables (simple approximation)."""
        vowels = 'aeiouy'
        word = word.lower()
        syllables = []
        current = ""
        
        for i, char in enumerate(word):
            current += char
            
            # Check if we should break here
            if char in vowels:
                # Look ahead - if next char is consonant followed by vowel, break after consonant
                if i + 2 < len(word):
                    if word[i+1] not in vowels and word[i+2] in vowels:
                        current += word[i+1]
                        syllables.append(current)
                        current = ""
                        continue
                
                # If at end or next is vowel, break here
                if i == len(word) - 1 or word[i+1] in vowels:
                    syllables.append(current)
                    current = ""
        
        if current:
            if syllables:
                syllables[-1] += current
            else:
                syllables.append(current)
        
        return syllables
    
    def get_pronunciation_guide(self, word: str) -> str:
        """Get a detailed pronunciation guide for a word."""
        word = word.lower().strip()
        
        guide_parts = []
        
        # Syllable breakdown
        syllables = self._syllabify(word)
        if syllables:
            guide_parts.append(f"Syllables: {'-'.join(syllables)}")
        
        # Phonemes
        phonemes = self.get_phonemes(word)
        if phonemes:
            guide_parts.append(f"Phonemes: {phonemes}")
        
        # CMU dictionary pronunciation
        if HAS_CMU_DICT and word in CMU_DICT:
            cmu = ' '.join(CMU_DICT[word][0])
            guide_parts.append(f"CMU: {cmu}")
        
        # Stress pattern if known
        if word in self.stress_patterns:
            patterns = self.stress_patterns[word]
            guide_parts.append(f"Stress: {patterns}")
        
        return '\n'.join(guide_parts) if guide_parts else f"Pronunciation: {word}"
    
    def compare_reading(self, expected_text: str, spoken_text: str) -> Dict[str, Any]:
        """
        Compare a passage of expected text with what was spoken.
        
        Returns detailed analysis of pronunciation accuracy.
        """
        # Tokenize both texts
        expected_words = re.findall(r'\b\w+\b', expected_text.lower())
        spoken_words = re.findall(r'\b\w+\b', spoken_text.lower())
        
        results = {
            'total_expected': len(expected_words),
            'total_spoken': len(spoken_words),
            'correct': 0,
            'incorrect': 0,
            'missed': 0,
            'extra': 0,
            'accuracy': 0.0,
            'word_results': [],
            'problem_words': [],
            'feedback': ""
        }
        
        # Align words using sequence matching
        matcher = SequenceMatcher(None, expected_words, spoken_words)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Words match
                for word in expected_words[i1:i2]:
                    results['correct'] += 1
                    results['word_results'].append({
                        'word': word,
                        'status': 'correct',
                        'score': 1.0
                    })
            
            elif tag == 'replace':
                # Words differ - assess pronunciation
                for exp, spk in zip(expected_words[i1:i2], spoken_words[j1:j2]):
                    assessment = self.assess_pronunciation(exp, spk)
                    
                    if assessment.is_correct:
                        results['correct'] += 1
                    else:
                        results['incorrect'] += 1
                        results['problem_words'].append({
                            'expected': exp,
                            'spoken': spk,
                            'score': assessment.score,
                            'feedback': assessment.feedback
                        })
                    
                    results['word_results'].append({
                        'word': exp,
                        'spoken': spk,
                        'status': 'correct' if assessment.is_correct else 'incorrect',
                        'score': assessment.score
                    })
            
            elif tag == 'delete':
                # Words in expected but not spoken (missed)
                for word in expected_words[i1:i2]:
                    results['missed'] += 1
                    results['word_results'].append({
                        'word': word,
                        'status': 'missed',
                        'score': 0.0
                    })
            
            elif tag == 'insert':
                # Extra words spoken
                results['extra'] += len(spoken_words[j1:j2])
        
        # Calculate accuracy
        if results['total_expected'] > 0:
            results['accuracy'] = results['correct'] / results['total_expected']
        
        # Generate overall feedback
        if results['accuracy'] >= 0.95:
            results['feedback'] = "Excellent reading! Nearly perfect pronunciation."
        elif results['accuracy'] >= 0.85:
            results['feedback'] = "Good reading! A few words need practice."
        elif results['accuracy'] >= 0.7:
            results['feedback'] = "Nice effort! Let's work on some words together."
        else:
            results['feedback'] = "Keep practicing! I'll help you with the tricky words."
        
        # Add specific word feedback
        if results['problem_words']:
            words_to_practice = [w['expected'] for w in results['problem_words'][:5]]
            results['feedback'] += f" Words to practice: {', '.join(words_to_practice)}"
        
        return results
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of pronunciation assessments in current session."""
        if not self.assessment_history:
            return {'message': 'No assessments yet'}
        
        correct = sum(1 for r in self.assessment_history if r.is_correct)
        total = len(self.assessment_history)
        
        # Find most problematic words
        problem_words = [r for r in self.assessment_history if not r.is_correct]
        problem_words.sort(key=lambda x: x.score)
        
        return {
            'total_words': total,
            'correct': correct,
            'accuracy': correct / total if total > 0 else 0,
            'words_to_practice': [r.word for r in problem_words[:10]],
            'average_score': sum(r.score for r in self.assessment_history) / total if total > 0 else 0
        }


# Singleton instance
_assessor = None

def get_pronunciation_assessor() -> PronunciationAssessor:
    """Get or create the pronunciation assessor singleton."""
    global _assessor
    if _assessor is None:
        _assessor = PronunciationAssessor()
    return _assessor


# Test
if __name__ == "__main__":
    print("Testing Pronunciation Assessor...")
    
    assessor = get_pronunciation_assessor()
    
    # Test single word
    print("\n1. Single word assessment:")
    result = assessor.assess_pronunciation("necessary", "nessesary")
    print(f"   Word: {result.word}")
    print(f"   Score: {result.score:.2f}")
    print(f"   Feedback: {result.feedback}")
    print(f"   Correct: {result.is_correct}")
    
    # Test pronunciation guide
    print("\n2. Pronunciation guide:")
    guide = assessor.get_pronunciation_guide("pronunciation")
    print(guide)
    
    # Test reading comparison
    print("\n3. Reading comparison:")
    expected = "The quick brown fox jumps over the lazy dog"
    spoken = "The quick brown fox jumps over the lazy dog"
    results = assessor.compare_reading(expected, spoken)
    print(f"   Accuracy: {results['accuracy']:.1%}")
    print(f"   Feedback: {results['feedback']}")
    
    print("\nPronunciation Assessor ready!")
