"""
Monica Grammar Checker with Challenge Memory
Listens to user's speech and corrects grammar mistakes.
Remembers repeated mistakes as "challenges" to help user improve.

Author: Monica AI
Date: December 2025
"""

import re
import json
import time
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Grammar checking library
HAS_LANGUAGE_TOOL = False
try:
    import language_tool_python
    HAS_LANGUAGE_TOOL = True
    print("[OK] LanguageTool loaded for grammar checking")
except ImportError:
    print("[WARNING] language_tool_python not available - using built-in rules")


@dataclass
class GrammarError:
    """Represents a grammar error."""
    text: str  # The incorrect text
    correction: str  # The suggested correction
    rule: str  # The grammar rule violated
    message: str  # Explanation
    position: int = 0  # Position in text
    category: str = "grammar"  # grammar, spelling, punctuation, style


@dataclass
class Challenge:
    """A recurring grammar challenge for the user."""
    rule: str
    category: str
    examples: List[str] = field(default_factory=list)
    corrections: List[str] = field(default_factory=list)
    occurrence_count: int = 1
    first_seen: str = ""
    last_seen: str = ""
    is_mastered: bool = False  # True if user hasn't made this mistake recently


class GrammarChecker:
    """
    Checks grammar and tracks user's challenges over time.
    """
    
    def __init__(self, data_dir: Path = None):
        self.language_tool = None
        
        # Initialize LanguageTool if available
        if HAS_LANGUAGE_TOOL:
            try:
                # Use local server for faster response
                self.language_tool = language_tool_python.LanguageTool('en-US')
                print("[GRAMMAR] LanguageTool initialized")
            except Exception as e:
                print(f"[GRAMMAR] LanguageTool init failed: {e}")
        
        # Data directory for storing challenges
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        # Challenge tracking
        self.challenges_file = self.data_dir / "grammar_challenges.json"
        self.challenges: Dict[str, Challenge] = {}
        self._load_challenges()
        
        # Session tracking
        self.session_errors: List[GrammarError] = []
        self.session_start = datetime.now()
        
        # Built-in grammar rules (used when LanguageTool not available)
        self.grammar_rules = self._init_grammar_rules()
        
        print(f"[GRAMMAR] Grammar checker initialized with {len(self.challenges)} tracked challenges")
    
    def _init_grammar_rules(self) -> Dict[str, Dict]:
        """Initialize built-in grammar rules."""
        return {
            # Subject-verb agreement
            'subject_verb_agreement': {
                'patterns': [
                    (r'\b(he|she|it)\s+(are|were|have)\b', 'Subject-verb agreement: "{0}" should use singular verb'),
                    (r'\b(they|we|you)\s+(is|was|has)\b', 'Subject-verb agreement: "{0}" should use plural verb'),
                    (r'\b(I)\s+(is|are|has)\b', 'Subject-verb agreement: "I" should use "am/was/have"'),
                ],
                'category': 'grammar'
            },
            
            # Common word confusions
            'word_confusion': {
                'patterns': [
                    (r'\b(your)\s+(welcome|right|wrong|the)\b', 'Did you mean "you\'re" (you are)?'),
                    (r'\b(its)\s+(a|an|the|going|been)\b', 'Did you mean "it\'s" (it is)?'),
                    (r'\b(there)\s+(going|coming|doing)\b', 'Did you mean "they\'re" (they are)?'),
                    (r'\b(their)\s+(is|are|was|were)\b', 'Did you mean "there" (location)?'),
                    (r'\b(then)\s+(I|you|we|they|he|she)\b', 'Did you mean "than" (comparison)?'),
                    (r'\b(affect)\s+(on|of)\b', 'Did you mean "effect" (noun)?'),
                    (r'\b(to)\s+(much|many|few)\b', 'Did you mean "too" (excessive)?'),
                    (r'\b(loose)\s+(my|your|the|weight)\b', 'Did you mean "lose" (misplace)?'),
                    (r'\b(could|would|should)\s+of\b', 'Should be "could/would/should have"'),
                ],
                'category': 'word_choice'
            },
            
            # Double negatives
            'double_negative': {
                'patterns': [
                    (r"\b(don't|doesn't|didn't|won't|can't|couldn't|wouldn't|shouldn't)\s+\w+\s+(no|nothing|nobody|nowhere|never)\b", 
                     'Double negative detected'),
                    (r"\b(ain't)\s+\w+\s+(no|nothing|nobody)\b", 'Double negative detected'),
                ],
                'category': 'grammar'
            },
            
            # Tense consistency
            'tense_issues': {
                'patterns': [
                    (r'\b(yesterday|last\s+\w+)\s+\w+\s+(is|are|am)\b', 'Past time reference with present tense'),
                    (r'\b(tomorrow|next\s+\w+)\s+\w+\s+(was|were|did)\b', 'Future time reference with past tense'),
                ],
                'category': 'grammar'
            },
            
            # Common mistakes
            'common_mistakes': {
                'patterns': [
                    (r'\b(alot)\b', '"A lot" should be two words'),
                    (r'\b(irregardless)\b', 'Use "regardless" instead'),
                    (r'\b(supposably)\b', 'Use "supposedly" instead'),
                    (r'\b(expresso)\b', 'Use "espresso" instead'),
                    (r'\b(excetera|ect)\b', 'Use "et cetera" or "etc."'),
                    (r'\b(definately|definatly)\b', 'Correct spelling is "definitely"'),
                    (r'\b(seperate)\b', 'Correct spelling is "separate"'),
                    (r'\b(occured)\b', 'Correct spelling is "occurred"'),
                    (r'\b(recieve)\b', 'Correct spelling is "receive"'),
                    (r'\b(wierd)\b', 'Correct spelling is "weird"'),
                    (r'\b(accomodate)\b', 'Correct spelling is "accommodate"'),
                    (r'\b(occassion)\b', 'Correct spelling is "occasion"'),
                    (r'\b(neccessary)\b', 'Correct spelling is "necessary"'),
                ],
                'category': 'spelling'
            },
            
            # Article usage
            'article_usage': {
                'patterns': [
                    (r'\b(a)\s+([aeiou]\w+)\b', 'Use "an" before words starting with vowel sounds'),
                    (r'\b(an)\s+([bcdfghjklmnpqrstvwxyz]\w+)\b', 'Use "a" before words starting with consonant sounds'),
                ],
                'category': 'grammar',
                'exceptions': ['a one', 'a once', 'a university', 'a union', 'a European', 
                              'an hour', 'an honest', 'an honor', 'an heir']
            },
            
            # Run-on sentences (simplified)
            'run_on': {
                'patterns': [
                    (r'[^.!?]{150,}', 'This might be a run-on sentence. Consider breaking it up.'),
                ],
                'category': 'style'
            },
        }
    
    def _load_challenges(self):
        """Load challenges from file."""
        if self.challenges_file.exists():
            try:
                with open(self.challenges_file, 'r') as f:
                    data = json.load(f)
                    for rule, challenge_data in data.items():
                        self.challenges[rule] = Challenge(**challenge_data)
                print(f"[GRAMMAR] Loaded {len(self.challenges)} challenges")
            except Exception as e:
                print(f"[GRAMMAR] Error loading challenges: {e}")
                self.challenges = {}
    
    def _save_challenges(self):
        """Save challenges to file."""
        try:
            data = {rule: asdict(challenge) for rule, challenge in self.challenges.items()}
            with open(self.challenges_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[GRAMMAR] Error saving challenges: {e}")
    
    def check_grammar(self, text: str) -> List[GrammarError]:
        """
        Check text for grammar errors.
        
        Args:
            text: The text to check
            
        Returns:
            List of GrammarError objects
        """
        errors = []
        
        # Use LanguageTool if available
        if self.language_tool:
            try:
                matches = self.language_tool.check(text)
                for match in matches:
                    try:
                        # Handle different attribute names in different versions
                        error_length = getattr(match, 'errorLength', None)
                        if error_length is None:
                            matched_text = getattr(match, 'matchedText', '')
                            error_length = len(matched_text) if matched_text else 10
                        
                        error_text = text[match.offset:match.offset + error_length]
                        
                        # Get rule ID (different attribute names in different versions)
                        rule_id = getattr(match, 'ruleId', None) or getattr(match, 'rule', {}).get('id', 'unknown')
                        
                        error = GrammarError(
                            text=error_text,
                            correction=match.replacements[0] if match.replacements else "",
                            rule=str(rule_id),
                            message=match.message,
                            position=match.offset,
                            category=getattr(match, 'category', 'grammar')
                        )
                        errors.append(error)
                        self._track_challenge(error)
                    except Exception as match_error:
                        # Skip problematic matches
                        pass
            except Exception as e:
                print(f"[GRAMMAR] LanguageTool error: {e}")
        
        # Also check with built-in rules
        builtin_errors = self._check_builtin_rules(text)
        
        # Merge errors (avoid duplicates)
        existing_positions = {e.position for e in errors}
        for error in builtin_errors:
            if error.position not in existing_positions:
                errors.append(error)
                self._track_challenge(error)
        
        self.session_errors.extend(errors)
        return errors
    
    def _check_builtin_rules(self, text: str) -> List[GrammarError]:
        """Check text against built-in grammar rules."""
        errors = []
        text_lower = text.lower()
        
        for rule_name, rule_data in self.grammar_rules.items():
            patterns = rule_data.get('patterns', [])
            category = rule_data.get('category', 'grammar')
            exceptions = rule_data.get('exceptions', [])
            
            for pattern, message in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    matched_text = match.group(0)
                    
                    # Check exceptions
                    if any(exc.lower() in matched_text.lower() for exc in exceptions):
                        continue
                    
                    error = GrammarError(
                        text=text[match.start():match.end()],
                        correction=self._suggest_correction(rule_name, matched_text),
                        rule=rule_name,
                        message=message.format(matched_text),
                        position=match.start(),
                        category=category
                    )
                    errors.append(error)
        
        return errors
    
    def _suggest_correction(self, rule: str, text: str) -> str:
        """Suggest a correction for a grammar error."""
        corrections = {
            'alot': 'a lot',
            'irregardless': 'regardless',
            'supposably': 'supposedly',
            'expresso': 'espresso',
            'definately': 'definitely',
            'definatly': 'definitely',
            'seperate': 'separate',
            'occured': 'occurred',
            'recieve': 'receive',
            'wierd': 'weird',
            'accomodate': 'accommodate',
            'occassion': 'occasion',
            'neccessary': 'necessary',
            'could of': 'could have',
            'would of': 'would have',
            'should of': 'should have',
        }
        
        text_lower = text.lower()
        for wrong, right in corrections.items():
            if wrong in text_lower:
                return text_lower.replace(wrong, right)
        
        return ""
    
    def _track_challenge(self, error: GrammarError):
        """Track a grammar error as a potential challenge."""
        rule = error.rule
        now = datetime.now().isoformat()
        
        if rule in self.challenges:
            # Update existing challenge
            challenge = self.challenges[rule]
            challenge.occurrence_count += 1
            challenge.last_seen = now
            
            # Add example if not already present
            if error.text not in challenge.examples:
                challenge.examples.append(error.text)
                if len(challenge.examples) > 10:
                    challenge.examples = challenge.examples[-10:]
            
            if error.correction and error.correction not in challenge.corrections:
                challenge.corrections.append(error.correction)
                if len(challenge.corrections) > 10:
                    challenge.corrections = challenge.corrections[-10:]
            
            # Mark as not mastered since it occurred again
            challenge.is_mastered = False
        else:
            # Create new challenge
            self.challenges[rule] = Challenge(
                rule=rule,
                category=error.category,
                examples=[error.text],
                corrections=[error.correction] if error.correction else [],
                occurrence_count=1,
                first_seen=now,
                last_seen=now,
                is_mastered=False
            )
        
        self._save_challenges()
    
    def get_challenge_feedback(self, error: GrammarError) -> str:
        """Get feedback about whether this is a recurring challenge."""
        rule = error.rule
        
        if rule in self.challenges:
            challenge = self.challenges[rule]
            count = challenge.occurrence_count
            
            if count >= 5:
                return f"[WARNING] This is a recurring challenge for you! You've made this mistake {count} times. Let's work on it together."
            elif count >= 3:
                return f"[Note] I've noticed this mistake {count} times before. It's becoming a pattern."
            elif count >= 2:
                return f"[Idea] You made this same mistake before. Remember: {error.message}"
        
        return ""
    
    def check_and_respond(self, text: str) -> Tuple[List[GrammarError], str]:
        """
        Check grammar and generate a helpful response.
        
        Returns:
            Tuple of (errors, response_text)
        """
        errors = self.check_grammar(text)
        
        if not errors:
            return [], ""
        
        response_parts = []
        
        for error in errors[:3]:  # Limit to 3 errors to avoid overwhelming
            # Basic correction
            correction_msg = f"'{error.text}' → '{error.correction}'" if error.correction else error.message
            
            # Check if it's a recurring challenge
            challenge_feedback = self.get_challenge_feedback(error)
            
            if challenge_feedback:
                response_parts.append(f"{challenge_feedback}\n{correction_msg}")
            else:
                response_parts.append(correction_msg)
        
        response = "\n".join(response_parts)
        return errors, response
    
    def get_challenges_summary(self) -> Dict[str, Any]:
        """Get a summary of user's grammar challenges."""
        if not self.challenges:
            return {'message': 'No grammar challenges tracked yet. Keep practicing!'}
        
        # Sort by occurrence count
        sorted_challenges = sorted(
            self.challenges.values(),
            key=lambda c: c.occurrence_count,
            reverse=True
        )
        
        top_challenges = []
        for c in sorted_challenges[:5]:
            top_challenges.append({
                'rule': c.rule,
                'count': c.occurrence_count,
                'category': c.category,
                'example': c.examples[-1] if c.examples else "",
                'correction': c.corrections[-1] if c.corrections else ""
            })
        
        total_errors = sum(c.occurrence_count for c in self.challenges.values())
        mastered = sum(1 for c in self.challenges.values() if c.is_mastered)
        
        return {
            'total_challenges': len(self.challenges),
            'total_errors': total_errors,
            'mastered': mastered,
            'top_challenges': top_challenges,
            'message': f"You have {len(self.challenges)} grammar areas to work on. Your top challenge is '{sorted_challenges[0].rule}' with {sorted_challenges[0].occurrence_count} occurrences."
        }
    
    def mark_challenge_mastered(self, rule: str):
        """Mark a challenge as mastered."""
        if rule in self.challenges:
            self.challenges[rule].is_mastered = True
            self._save_challenges()
    
    def get_practice_suggestions(self) -> List[str]:
        """Get suggestions for grammar practice based on challenges."""
        suggestions = []
        
        # Get top unmastered challenges
        unmastered = [c for c in self.challenges.values() if not c.is_mastered]
        unmastered.sort(key=lambda c: c.occurrence_count, reverse=True)
        
        for challenge in unmastered[:3]:
            if challenge.examples and challenge.corrections:
                example = challenge.examples[-1]
                correction = challenge.corrections[-1]
                suggestions.append(f"Practice: '{example}' should be '{correction}'")
        
        return suggestions
    
    def cleanup(self):
        """Cleanup resources."""
        if self.language_tool:
            try:
                self.language_tool.close()
            except:
                pass


# Singleton instance
_grammar_checker = None

def get_grammar_checker() -> GrammarChecker:
    """Get or create the grammar checker singleton."""
    global _grammar_checker
    if _grammar_checker is None:
        _grammar_checker = GrammarChecker()
    return _grammar_checker


# Test
if __name__ == "__main__":
    print("Testing Grammar Checker...")
    
    checker = get_grammar_checker()
    
    # Test sentences with errors
    test_sentences = [
        "I could of went to the store.",
        "Your the best person I know.",
        "He don't know nothing about it.",
        "I definately want to go their.",
        "Me and him went to the store.",
        "The data is very importent.",
    ]
    
    for sentence in test_sentences:
        print(f"\nChecking: '{sentence}'")
        errors, response = checker.check_and_respond(sentence)
        if response:
            print(f"Response: {response}")
        else:
            print("No errors found.")
    
    # Show challenges summary
    print("\n" + "="*50)
    summary = checker.get_challenges_summary()
    print(f"Challenges Summary: {summary['message']}")
    
    print("\nGrammar Checker ready!")
