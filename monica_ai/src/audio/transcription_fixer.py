"""
Transcription Post-Processing for Monica AI
Fixes common misheard words and improves accuracy
"""
import re
from typing import Dict, List, Tuple

class TranscriptionFixer:
    """Fix common transcription errors from Whisper."""
    
    def __init__(self):
        """Initialize with common corrections."""
        # Common misheard words/names
        # Based on OpenAI Whisper Prompting Guide - use glossary approach
        self.word_corrections = {
            # Monica variations (most common mishearings)
            r'\bmonaco\b': 'Monica',
            r'\bmania\b': 'Monica',
            r'\bmonica\'s\b': 'Monica',
            r'\bmoniker\b': 'Monica',
            r'\bmanic\b': 'Monica',
            r'\bmarnica\b': 'Monica',
            r'\bmonika\b': 'Monica',
            r'\bmonica\b': 'Monica',
            r'\bmon ica\b': 'Monica',
            r'\bmoney ca\b': 'Monica',
            r'\bmoneca\b': 'Monica',
            r'\bmonaca\b': 'Monica',
            r'\bmonica,\b': 'Monica',
            r'\bm+onica\b': 'Monica',
            
            # Common greeting fixes
            r'\bhey money\b': 'hey Monica',
            r'\bhi money\b': 'hi Monica',
            r'\bhello money\b': 'hello Monica',
            r'\bhey monic\b': 'hey Monica',
            r'\ba monica\b': 'hey Monica',
            
            # Initialize variations
            r'\binitialize\b': 'initialize',
            r'\binitialise\b': 'initialize',
            r'\binit\b': 'initialize',
            
            # Date/Time questions
            r'\bwhat\'s state\b': 'what\'s the date',
            r'\bwhat state\b': 'what\'s the date',
            r'\btoday state\b': 'today\'s date',
            r'\bwhat is today state\b': 'what is today\'s date',
            r'\bwhat\'s today\b': 'what\'s the date today',

            # "today's date" corrupted variants seen in practice
            r'\btdyst\b': "today's date",
            r'\btodaisy\b': "today's date",
            r'\btodaisy\b': "today's date",
            r'\bdaysdate\b': "day's date",

            # Joined artifacts
            r'\bistdyst\b': "is today's date",
            
            # Common phrases
            r'\bthink you\b': 'thank you',
            r'\btank you\b': 'thank you',
            r'\byour welcome\b': 'you\'re welcome',
            r'\bcan you here me\b': 'can you hear me',
            r'\bhere me\b': 'hear me',
            
            # Technical terms
            r'\bpython\b': 'Python',
            r'\bjavascript\b': 'JavaScript',
            r'\bai\b': 'AI',
            r'\bar window\b': 'AR window',
            r'\bar\b': 'AR',
            
            # Common commands
            r'\bstop monica\b': 'stop Monica',
            r'\bmonika stop\b': 'Monica stop',
            r'\bmonika please\b': 'Monica please',
            r'\bstop it\b': 'stop',
            r'\bshut up\b': 'stop',
            r'\bquiet\b': 'stop',
            r'\bsilence\b': 'stop',
            
            # Vision commands
            r'\bnight vision\b': 'night vision',
            r'\bthermal vision\b': 'thermal vision',
            r'\bheat vision\b': 'thermal vision',
            
            # Yes/No variations
            r'\byeah\b': 'yes',
            r'\byep\b': 'yes',
            r'\byup\b': 'yes',
            r'\bnope\b': 'no',
            r'\bnah\b': 'no',
            
            # Creator name
            r'\bmjp\b': 'MJP',
            r'\bm\s*jp\b': 'MJP',
            r'\bmarvin\b': 'Marvin',

            # Historical figures
            r'\bcrispicolontis\b': 'Christopher Columbus',
            r'\bcrispicalontes\b': 'Christopher Columbus',
            r'\bchristopher\s*columbus\b': 'Christopher Columbus',
            r'\bcristopher\s*columbus\b': 'Christopher Columbus',
            r'\bcolumbus\b': 'Columbus',
            r'\bcolombis\b': 'Columbus',
            
            # Common misrecognitions
            r'\bcouncing\b': 'counseling',
            r'\bcounceling\b': 'counseling',
            r'\bpsycology\b': 'psychology',
            r'\bsychology\b': 'psychology',
            r'\bpsychological\b': 'psychological',
            r'\bpsycological\b': 'psychological',
            r'\bpsycho\b': 'psychological',  # Common mishearing
            r'\bmytyoerth\b': 'my date of birth',
            r'\bmydateaverg\b': 'my date of birth',

            # Common split/join artifacts
            r'\bdevelop mental\b': 'developmental',
            r'\bneu ropsych ology\b': 'neuropsychology',
        }
        
        # Phrase-level corrections (more context)
        self.phrase_corrections = [
            # Date/time patterns
            (r'what is (?:the )?today[\'s]? (?:state|stay|date)', 'what is today\'s date'),
            (r'what istdyst', "what is today's date"),
            (r'what is (?:the )?two days ?date', "what is today's date"),
            (r'what is (?:the )?today ?s ?date', "what is today's date"),
            (r'what is tod(?:ay|ai)sy', "what is today's date"),
            (r'what[\'s]? (?:the )?time (?:is it|now)', 'what time is it'),
            (r'tell me (?:the )?time', 'tell me the time'),
            
            # Monica commands
            (r'(?:hey|hi|hello) (?:monaco|mania|manic)', 'hey Monica'),
            (r'(?:monaco|mania) initialize', 'Monica initialize'),
            
            # Common questions
            (r'how are you (?:doing|today)', 'how are you doing'),
            (r'can you help (?:me|with)', 'can you help me'),

            # Live streaming toggle (common ASR error)
            (r'no life streaming', 'not live streaming'),
        ]
        
        # Grammar fixes
        self.grammar_fixes = [
            # Fix double spaces
            (r'\s+', ' '),
            # Fix sentence capitalization
            (r'^([a-z])', lambda m: m.group(1).upper()),
            # Fix I lowercase
            (r'\bi\b', 'I'),
            # Fix punctuation spacing
            (r'\s+([.,!?])', r'\1'),
            (r'([.,!?])([A-Za-z])', r'\1 \2'),
        ]
    
    def fix_transcription(self, text: str) -> str:
        """
        Apply all fixes to transcription text.
        """
        if not text:
            return text
        
        original = text
        text = text.strip()
        
        # Apply word-level corrections (case-insensitive)
        for pattern, replacement in self.word_corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Apply phrase-level corrections
        for pattern, replacement in self.phrase_corrections:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Apply grammar fixes
        for pattern, replacement in self.grammar_fixes:
            if callable(replacement):
                text = re.sub(pattern, replacement, text)
            else:
                text = re.sub(pattern, replacement, text)
        
        # Ensure proper sentence ending
        if text and text[-1] not in '.!?':
            # If it looks like a question
            if text.lower().startswith(('what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'can', 'could', 'will', 'would')):
                text += '?'
            else:
                text += '.'
        
        # Clean up
        text = text.strip()
        
        # Log if we made changes
        if text != original:
            print(f"[TRANSCRIPTION FIX] '{original}' → '{text}'")
        
        return text
    
    def learn_correction(self, wrong: str, correct: str):
        """
        Learn a new correction from user feedback.
        """
        # Add to word corrections
        pattern = r'\b' + re.escape(wrong.lower()) + r'\b'
        self.word_corrections[pattern] = correct
        print(f"[TRANSCRIPTION FIX] Learned: '{wrong}' → '{correct}'")

# Global instance
_transcription_fixer = None

def get_transcription_fixer():
    """Get or create transcription fixer."""
    global _transcription_fixer
    if _transcription_fixer is None:
        _transcription_fixer = TranscriptionFixer()
    return _transcription_fixer
