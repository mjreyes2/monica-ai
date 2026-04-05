"""
Monica AI - English Teacher Module

Comprehensive English teaching system:
- Grammar correction and explanation
- Vocabulary building with spaced repetition
- Pronunciation guidance
- Writing feedback (grammar, style, clarity)
- Literature comprehension discussion
- Quiz system (multiple choice, fill-in-blank, definition matching)
- Persistent memory of difficult words per user

All data stored locally in data/user_profile/vocabulary_progress.json
"""

import json
import time
import random
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("Monica.EnglishTeacher")


@dataclass
class VocabWord:
    """A vocabulary word being tracked."""
    word: str
    definition: str
    example_sentence: str
    difficulty: int = 1  # 1-5
    times_seen: int = 0
    times_correct: int = 0
    times_wrong: int = 0
    last_seen: float = 0.0
    mastered: bool = False
    category: str = ""
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)


@dataclass
class QuizResult:
    """Result of a quiz session."""
    timestamp: float
    total_questions: int
    correct: int
    wrong: int
    words_tested: List[str]
    score_percent: float


class EnglishTeacher:
    """
    Monica's English teaching system.
    Tracks vocabulary progress, generates quizzes, provides grammar feedback.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            from config.settings import config
            data_dir = Path(config.BASE_DIR) / "data" / "user_profile"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vocab_file = self.data_dir / "vocabulary_progress.json"
        self.quiz_history_file = self.data_dir / "quiz_history.json"
        
        # Vocabulary database
        self.vocab: Dict[str, VocabWord] = {}
        self.quiz_history: List[QuizResult] = []
        
        # Load existing progress
        self._load_progress()
        
        # Grammar rules database
        self.grammar_rules = self._init_grammar_rules()
        
        # Common confused words
        self.confused_words = self._init_confused_words()
        
        # Vocabulary word bank (built-in starter words)
        self.word_bank = self._init_word_bank()
        
        logger.info(f"[ENGLISH] Teacher initialized ({len(self.vocab)} tracked words, "
                     f"{len(self.quiz_history)} past quizzes)")

    def _load_progress(self):
        """Load vocabulary progress from disk."""
        if self.vocab_file.exists():
            try:
                with open(str(self.vocab_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for word_data in data.get("vocabulary", []):
                    w = VocabWord(**word_data)
                    self.vocab[w.word.lower()] = w
            except Exception as e:
                logger.warning(f"[ENGLISH] Could not load vocab progress: {e}")
        
        if self.quiz_history_file.exists():
            try:
                with open(str(self.quiz_history_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for qr in data.get("history", []):
                    self.quiz_history.append(QuizResult(**qr))
            except Exception as e:
                logger.debug(f"[ENGLISH] Could not load quiz history: {e}")

    def save_progress(self):
        """Save vocabulary progress to disk."""
        try:
            vocab_data = {"vocabulary": [asdict(w) for w in self.vocab.values()]}
            with open(str(self.vocab_file), 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, indent=2)
            
            quiz_data = {"history": [asdict(q) for q in self.quiz_history[-100:]]}
            with open(str(self.quiz_history_file), 'w', encoding='utf-8') as f:
                json.dump(quiz_data, f, indent=2)
        except Exception as e:
            logger.error(f"[ENGLISH] Could not save progress: {e}")

    # ---- Vocabulary Tracking ----

    def add_difficult_word(self, word: str, definition: str = "",
                           example: str = "", category: str = "") -> str:
        """Add a word the user had trouble with."""
        key = word.lower().strip()
        if key in self.vocab:
            self.vocab[key].times_seen += 1
            self.vocab[key].last_seen = time.time()
            self.save_progress()
            return f"Updated '{word}' - seen {self.vocab[key].times_seen} times now."
        
        if not definition:
            definition = self._lookup_definition(key)
        if not example:
            example = self._generate_example(key)
        
        self.vocab[key] = VocabWord(
            word=key,
            definition=definition,
            example_sentence=example,
            category=category,
            last_seen=time.time(),
            times_seen=1
        )
        self.save_progress()
        return f"Added '{word}' to your vocabulary list. I'll quiz you on it later!"

    def mark_correct(self, word: str):
        """Mark a word as correctly answered in a quiz."""
        key = word.lower().strip()
        if key in self.vocab:
            self.vocab[key].times_correct += 1
            self.vocab[key].last_seen = time.time()
            # Mastered if correct 5+ times with >80% accuracy
            w = self.vocab[key]
            total = w.times_correct + w.times_wrong
            if w.times_correct >= 5 and total > 0 and w.times_correct / total >= 0.8:
                w.mastered = True
            self.save_progress()

    def mark_wrong(self, word: str):
        """Mark a word as incorrectly answered."""
        key = word.lower().strip()
        if key in self.vocab:
            self.vocab[key].times_wrong += 1
            self.vocab[key].last_seen = time.time()
            self.vocab[key].mastered = False
            self.save_progress()

    def get_difficult_words(self) -> List[VocabWord]:
        """Get words the user struggles with most (sorted by error rate)."""
        struggling = []
        for w in self.vocab.values():
            if not w.mastered and w.times_seen > 0:
                total = w.times_correct + w.times_wrong
                error_rate = w.times_wrong / max(total, 1)
                struggling.append((error_rate, w))
        struggling.sort(key=lambda x: x[0], reverse=True)
        return [w for _, w in struggling[:20]]

    def get_mastered_words(self) -> List[VocabWord]:
        """Get words the user has mastered."""
        return [w for w in self.vocab.values() if w.mastered]

    def get_vocab_stats(self) -> Dict[str, Any]:
        """Get vocabulary learning statistics."""
        total = len(self.vocab)
        mastered = sum(1 for w in self.vocab.values() if w.mastered)
        struggling = len(self.get_difficult_words())
        
        recent_quizzes = self.quiz_history[-10:]
        avg_score = 0
        if recent_quizzes:
            avg_score = sum(q.score_percent for q in recent_quizzes) / len(recent_quizzes)
        
        return {
            "total_words": total,
            "mastered": mastered,
            "struggling": struggling,
            "in_progress": total - mastered,
            "total_quizzes": len(self.quiz_history),
            "avg_recent_score": round(avg_score, 1),
        }

    # ---- Quiz System ----

    def generate_quiz(self, num_questions: int = 5, 
                      quiz_type: str = "mixed") -> List[Dict[str, Any]]:
        """
        Generate a vocabulary quiz.
        
        quiz_type: 'definition', 'fill_blank', 'synonym', 'mixed'
        Returns list of question dicts.
        """
        # Prioritize words user struggles with + words not seen recently
        candidates = list(self.vocab.values())
        if not candidates:
            # Use word bank if no tracked words yet
            candidates = self._get_word_bank_samples(num_questions)
        
        # Sort by: not mastered first, then by least recently seen
        candidates.sort(key=lambda w: (w.mastered, w.last_seen))
        selected = candidates[:min(num_questions * 2, len(candidates))]
        random.shuffle(selected)
        selected = selected[:num_questions]
        
        questions = []
        types = ['definition', 'fill_blank', 'synonym']
        
        for i, word in enumerate(selected):
            if quiz_type == 'mixed':
                qt = types[i % len(types)]
            else:
                qt = quiz_type
            
            if qt == 'definition':
                q = self._make_definition_question(word)
            elif qt == 'fill_blank':
                q = self._make_fill_blank_question(word)
            elif qt == 'synonym':
                q = self._make_synonym_question(word)
            else:
                q = self._make_definition_question(word)
            
            questions.append(q)
        
        return questions

    def _make_definition_question(self, word: VocabWord) -> Dict[str, Any]:
        """Create a 'what does this word mean?' question."""
        correct = word.definition
        # Generate wrong answers
        distractors = self._get_distractors(word, 3)
        options = [correct] + distractors
        random.shuffle(options)
        
        return {
            "type": "definition",
            "question": f"What does '{word.word}' mean?",
            "word": word.word,
            "options": options,
            "correct_answer": correct,
            "correct_index": options.index(correct),
            "example": word.example_sentence,
        }

    def _make_fill_blank_question(self, word: VocabWord) -> Dict[str, Any]:
        """Create a fill-in-the-blank question."""
        sentence = word.example_sentence
        if word.word.lower() in sentence.lower():
            blank_sentence = re.sub(
                re.escape(word.word), "_____", sentence, flags=re.IGNORECASE)
        else:
            blank_sentence = f"The _____ was evident in the situation. (hint: {word.definition[:40]})"
        
        return {
            "type": "fill_blank",
            "question": f"Fill in the blank: {blank_sentence}",
            "word": word.word,
            "correct_answer": word.word,
            "hint": word.definition[:60],
        }

    def _make_synonym_question(self, word: VocabWord) -> Dict[str, Any]:
        """Create a synonym matching question."""
        if word.synonyms:
            correct = word.synonyms[0]
        else:
            correct = word.definition.split(',')[0].strip()[:30]
        
        distractors = self._get_distractors(word, 3)
        options = [correct] + distractors
        random.shuffle(options)
        
        return {
            "type": "synonym",
            "question": f"Which is closest in meaning to '{word.word}'?",
            "word": word.word,
            "options": options,
            "correct_answer": correct,
            "correct_index": options.index(correct),
        }

    def score_quiz(self, questions: List[Dict], answers: List[str]) -> QuizResult:
        """Score a completed quiz and update word tracking."""
        correct = 0
        wrong = 0
        words_tested = []
        
        for q, a in zip(questions, answers):
            word = q["word"]
            words_tested.append(word)
            
            if q["type"] == "fill_blank":
                is_correct = a.lower().strip() == q["correct_answer"].lower().strip()
            else:
                is_correct = a.lower().strip() == q["correct_answer"].lower().strip()
            
            if is_correct:
                correct += 1
                self.mark_correct(word)
            else:
                wrong += 1
                self.mark_wrong(word)
        
        total = correct + wrong
        score = (correct / total * 100) if total > 0 else 0
        
        result = QuizResult(
            timestamp=time.time(),
            total_questions=total,
            correct=correct,
            wrong=wrong,
            words_tested=words_tested,
            score_percent=score,
        )
        self.quiz_history.append(result)
        self.save_progress()
        return result

    # ---- Grammar Checking ----

    def check_grammar(self, text: str) -> List[Dict[str, str]]:
        """
        Check text for common grammar issues.
        Returns list of {issue, suggestion, rule} dicts.
        """
        issues = []
        
        for rule_name, rule in self.grammar_rules.items():
            pattern = rule["pattern"]
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "issue": match.group(),
                    "position": match.start(),
                    "suggestion": rule["suggestion"],
                    "rule": rule["explanation"],
                    "category": rule.get("category", "grammar"),
                })
        
        # Check confused words
        words = text.lower().split()
        for i, word in enumerate(words):
            if word in self.confused_words:
                context = " ".join(words[max(0, i-3):min(len(words), i+4)])
                issues.append({
                    "issue": word,
                    "position": text.lower().find(word),
                    "suggestion": self.confused_words[word]["tip"],
                    "rule": self.confused_words[word]["explanation"],
                    "category": "commonly confused",
                })
        
        return issues

    def get_writing_feedback(self, text: str) -> Dict[str, Any]:
        """Provide comprehensive writing feedback."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = text.split()
        word_count = len(words)
        avg_sentence_len = word_count / max(len(sentences), 1)
        
        # Vocabulary diversity
        unique_words = set(w.lower() for w in words)
        vocab_diversity = len(unique_words) / max(word_count, 1)
        
        # Grammar issues
        grammar_issues = self.check_grammar(text)
        
        # Track difficult words found
        difficult_in_text = []
        for w in unique_words:
            if w in self.vocab and not self.vocab[w].mastered:
                difficult_in_text.append(w)
        
        feedback = {
            "word_count": word_count,
            "sentence_count": len(sentences),
            "avg_sentence_length": round(avg_sentence_len, 1),
            "vocabulary_diversity": round(vocab_diversity * 100, 1),
            "grammar_issues": grammar_issues,
            "grammar_issue_count": len(grammar_issues),
            "difficult_words_used": difficult_in_text,
            "suggestions": [],
        }
        
        # Style suggestions
        if avg_sentence_len > 25:
            feedback["suggestions"].append(
                "Some sentences are very long. Try breaking them into shorter ones for clarity.")
        if avg_sentence_len < 8:
            feedback["suggestions"].append(
                "Your sentences are quite short. Try combining some for better flow.")
        if vocab_diversity < 0.4:
            feedback["suggestions"].append(
                "Try using more varied vocabulary to make your writing more engaging.")
        if word_count < 50:
            feedback["suggestions"].append(
                "Consider expanding your ideas with more detail and examples.")
        
        return feedback

    # ---- Pronunciation Help ----

    def get_pronunciation_guide(self, word: str) -> Dict[str, str]:
        """Get pronunciation guidance for a word."""
        # Common pronunciation patterns
        guides = {
            "colonel": {"phonetic": "KER-nul", "tip": "The 'l' is silent, pronounced like 'kernel'"},
            "February": {"phonetic": "FEB-roo-air-ee", "tip": "Don't skip the first 'r'"},
            "library": {"phonetic": "LY-brair-ee", "tip": "Two syllables with 'r': li-BRAR-y"},
            "probably": {"phonetic": "PROB-uh-blee", "tip": "Three syllables, not 'prolly'"},
            "comfortable": {"phonetic": "KUMF-ter-bull", "tip": "Often shortened to 3 syllables in speech"},
            "temperature": {"phonetic": "TEM-per-uh-chur", "tip": "Four syllables, don't skip 'per'"},
            "nuclear": {"phonetic": "NOO-klee-er", "tip": "Three syllables, NOT 'noo-kyoo-ler'"},
            "espresso": {"phonetic": "eh-SPRES-oh", "tip": "No 'x' sound - it's 'es', not 'ex'"},
            "mischievous": {"phonetic": "MIS-chuh-vus", "tip": "Three syllables, NOT four"},
            "particularly": {"phonetic": "par-TIK-yoo-lar-lee", "tip": "Five syllables, stress on second"},
        }
        
        key = word.lower().strip()
        if key in guides:
            return guides[key]
        
        # Generate basic phonetic guide
        return {
            "phonetic": self._basic_phonetic(key),
            "tip": f"Break it down syllable by syllable: {self._syllabify(key)}"
        }

    def _basic_phonetic(self, word: str) -> str:
        """Generate a basic phonetic representation."""
        # Simple heuristic - not perfect but helpful
        result = word.upper()
        result = result.replace("PH", "F")
        result = result.replace("GH", "")
        result = result.replace("TION", "SHUN")
        result = result.replace("SION", "ZHUN")
        result = result.replace("IGHT", "YTE")
        return result

    def _syllabify(self, word: str) -> str:
        """Simple syllable splitting."""
        vowels = "aeiouy"
        syllables = []
        current = ""
        prev_vowel = False
        
        for c in word:
            current += c
            is_vowel = c.lower() in vowels
            if prev_vowel and not is_vowel and len(current) > 1:
                syllables.append(current[:-1])
                current = c
            prev_vowel = is_vowel
        
        if current:
            syllables.append(current)
        
        return "-".join(syllables) if syllables else word

    # ---- Context for AI Prompt ----

    def get_teaching_context(self) -> str:
        """Get context string for AI prompt about English teaching."""
        stats = self.get_vocab_stats()
        difficult = self.get_difficult_words()[:5]
        
        context_parts = []
        context_parts.append(
            f"[ENGLISH TEACHER] Tracking {stats['total_words']} vocabulary words. "
            f"Mastered: {stats['mastered']}, Struggling: {stats['struggling']}.")
        
        if difficult:
            words_str = ", ".join(f"'{w.word}'" for w in difficult)
            context_parts.append(f"User struggles with: {words_str}. "
                                  "Naturally incorporate these into conversation.")
        
        if stats['total_quizzes'] > 0:
            context_parts.append(
                f"Quiz history: {stats['total_quizzes']} quizzes, "
                f"recent avg score: {stats['avg_recent_score']}%.")
        
        context_parts.append(
            "As an English teacher, you help with grammar, vocabulary, writing, "
            "literature comprehension, and pronunciation. You remember words the user "
            "struggles with and quiz them periodically.")
        
        return "\n".join(context_parts)

    # ---- Internal helpers ----

    def _get_distractors(self, word: VocabWord, count: int) -> List[str]:
        """Get wrong answer options for quiz questions."""
        all_defs = [w.definition for w in self.vocab.values() 
                    if w.word != word.word and w.definition]
        
        if len(all_defs) < count:
            # Add from word bank
            for cat, words in self.word_bank.items():
                for w, d, e in words:
                    if w != word.word:
                        all_defs.append(d)
        
        random.shuffle(all_defs)
        return all_defs[:count]

    def _lookup_definition(self, word: str) -> str:
        """Look up a word definition from built-in bank."""
        for cat, words in self.word_bank.items():
            for w, d, e in words:
                if w.lower() == word.lower():
                    return d
        return f"Definition of '{word}' (look up for full meaning)"

    def _generate_example(self, word: str) -> str:
        """Generate example sentence."""
        for cat, words in self.word_bank.items():
            for w, d, e in words:
                if w.lower() == word.lower():
                    return e
        return f"The word '{word}' can be used in various contexts."

    def _get_word_bank_samples(self, count: int) -> List[VocabWord]:
        """Get sample words from the built-in word bank."""
        samples = []
        for cat, words in self.word_bank.items():
            for w, d, e in words:
                samples.append(VocabWord(
                    word=w, definition=d, example_sentence=e,
                    category=cat, difficulty=2
                ))
        random.shuffle(samples)
        return samples[:count]

    def _init_grammar_rules(self) -> Dict[str, Dict]:
        """Initialize common grammar error patterns."""
        return {
            "their_there_theyre": {
                "pattern": r"\btheir\s+(is|are|was|were)\b",
                "suggestion": "Use 'there' for location/existence, 'their' for possession",
                "explanation": "'Their' shows possession (their car). 'There' shows location (over there) or existence (there is).",
                "category": "homophones",
            },
            "your_youre": {
                "pattern": r"\byour\s+(a|an|the|very|so|too|quite|really)\s+(good|great|nice|smart|kind|funny|beautiful|amazing|wonderful)",
                "suggestion": "Did you mean 'you're' (you are)?",
                "explanation": "'Your' shows possession (your book). 'You're' = 'you are' (you're great).",
                "category": "homophones",
            },
            "its_its": {
                "pattern": r"\bit's\s+(own|self|color|size|weight|name|purpose)\b",
                "suggestion": "Use 'its' (no apostrophe) for possession",
                "explanation": "'It's' = 'it is'. 'Its' (no apostrophe) = possession (the dog wagged its tail).",
                "category": "apostrophes",
            },
            "double_negative": {
                "pattern": r"\b(don't|doesn't|didn't|can't|won't|isn't|aren't|wasn't|weren't)\s+\w+\s+(no|nothing|nobody|nowhere|neither|never)\b",
                "suggestion": "Avoid double negatives - use one negative word",
                "explanation": "Double negatives cancel each other out. Say 'I don't have any' not 'I don't have none'.",
                "category": "negation",
            },
            "could_of": {
                "pattern": r"\b(could|would|should|must|might)\s+of\b",
                "suggestion": "Use 'have' instead of 'of' (could have, would have)",
                "explanation": "'Could of' is incorrect. The correct form is 'could have' (often contracted to could've).",
                "category": "common_errors",
            },
            "alot": {
                "pattern": r"\balot\b",
                "suggestion": "'A lot' is two words, not one",
                "explanation": "'Alot' is not a word. It should be 'a lot' (two words). 'Allot' means to distribute.",
                "category": "spelling",
            },
            "supposably": {
                "pattern": r"\bsupposably\b",
                "suggestion": "The correct word is 'supposedly'",
                "explanation": "'Supposedly' means 'according to what is believed'. 'Supposably' is non-standard.",
                "category": "pronunciation_spelling",
            },
            "irregardless": {
                "pattern": r"\birregardless\b",
                "suggestion": "Use 'regardless' instead",
                "explanation": "'Irregardless' is non-standard. Use 'regardless' (the 'ir-' prefix is redundant).",
                "category": "word_choice",
            },
            "subject_verb_none": {
                "pattern": r"\bnone\s+(are|were|have)\b",
                "suggestion": "'None' is typically singular: 'none is', 'none was', 'none has'",
                "explanation": "'None' often takes a singular verb (none of them is ready), though plural is accepted in informal use.",
                "category": "subject_verb_agreement",
            },
        }

    def _init_confused_words(self) -> Dict[str, Dict]:
        """Common confused word pairs."""
        return {
            "affect": {
                "tip": "'Affect' is usually a verb (to influence). 'Effect' is usually a noun (the result).",
                "explanation": "The rain will AFFECT the game. The EFFECT of the rain was a delay.",
            },
            "effect": {
                "tip": "'Effect' is usually a noun (result). 'Affect' is usually a verb (to influence).",
                "explanation": "The EFFECT was dramatic. The news AFFECTED everyone.",
            },
            "then": {
                "tip": "'Then' = time/sequence. 'Than' = comparison.",
                "explanation": "First this, THEN that (time). Better THAN that (comparison).",
            },
            "than": {
                "tip": "'Than' = comparison. 'Then' = time/sequence.",
                "explanation": "More THAN enough (comparison). Back THEN (time).",
            },
            "loose": {
                "tip": "'Loose' = not tight. 'Lose' = to misplace or fail to win.",
                "explanation": "The screw is LOOSE. Don't LOSE your keys.",
            },
            "lose": {
                "tip": "'Lose' = to misplace. 'Loose' = not tight.",
                "explanation": "Did you LOSE something? That shirt is too LOOSE.",
            },
            "principal": {
                "tip": "'Principal' = main/school leader. 'Principle' = rule/belief.",
                "explanation": "The PRINCIPAL of the school (person). A guiding PRINCIPLE (rule).",
            },
            "principle": {
                "tip": "'Principle' = rule/belief. 'Principal' = main/school leader.",
                "explanation": "Moral PRINCIPLES (beliefs). The PRINCIPAL reason (main).",
            },
        }

    def _init_word_bank(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """Built-in vocabulary word bank: (word, definition, example)."""
        return {
            "academic": [
                ("ubiquitous", "present, appearing, or found everywhere",
                 "Smartphones have become ubiquitous in modern society."),
                ("paradigm", "a typical example or pattern; a model",
                 "The discovery shifted the scientific paradigm completely."),
                ("pragmatic", "dealing with things sensibly and realistically",
                 "She took a pragmatic approach to solving the budget crisis."),
                ("ambiguous", "open to more than one interpretation; unclear",
                 "The contract language was ambiguous and caused confusion."),
                ("meticulous", "showing great attention to detail; very careful",
                 "The scientist was meticulous in recording her observations."),
                ("eloquent", "fluent or persuasive in speaking or writing",
                 "The lawyer delivered an eloquent closing argument."),
                ("resilient", "able to recover quickly from difficulties",
                 "Children are remarkably resilient after setbacks."),
                ("profound", "very great or intense; having deep insight",
                 "The book had a profound impact on her worldview."),
                ("concise", "giving information clearly and in few words",
                 "Please keep your report concise and to the point."),
                ("benevolent", "well-meaning and kindly; charitable",
                 "The benevolent donor funded the entire scholarship program."),
            ],
            "everyday": [
                ("diligent", "having or showing care in one's work",
                 "She was a diligent student who always completed her homework."),
                ("empathy", "the ability to understand another's feelings",
                 "Showing empathy helps build stronger relationships."),
                ("persevere", "to continue despite difficulty or opposition",
                 "You must persevere even when the task seems impossible."),
                ("versatile", "able to adapt to many different functions",
                 "A versatile tool can be used for many different jobs."),
                ("authentic", "genuine; not a copy or imitation",
                 "The restaurant serves authentic Italian cuisine."),
                ("elaborate", "detailed and complicated; to explain further",
                 "Could you elaborate on your plan for the project?"),
                ("inevitable", "certain to happen; unavoidable",
                 "Change is inevitable in any growing organization."),
                ("substantial", "of considerable importance, size, or worth",
                 "The company made a substantial investment in new technology."),
                ("articulate", "able to express thoughts clearly and effectively",
                 "She is very articulate when presenting her ideas."),
                ("comprehensive", "complete; including all elements",
                 "The study provided a comprehensive overview of the topic."),
            ],
            "advanced": [
                ("ephemeral", "lasting for a very short time",
                 "The beauty of cherry blossoms is ephemeral, lasting only days."),
                ("juxtaposition", "placing things close together for comparison",
                 "The juxtaposition of wealth and poverty was striking."),
                ("surreptitious", "kept secret, especially due to disapproval",
                 "He cast a surreptitious glance at the exam answers."),
                ("nomenclature", "the system of names used in a field",
                 "Medical nomenclature can be confusing for patients."),
                ("dichotomy", "a division into two contrasting things",
                 "There is a false dichotomy between art and science."),
                ("esoteric", "intended for a small group with special knowledge",
                 "The professor's lecture on quantum topology was quite esoteric."),
                ("perfunctory", "carried out with minimum effort; superficial",
                 "He gave a perfunctory nod before returning to his work."),
                ("recalcitrant", "stubbornly uncooperative",
                 "The recalcitrant student refused to follow the rules."),
                ("ameliorate", "to make something bad better; improve",
                 "The new policies should ameliorate the housing crisis."),
                ("obfuscate", "to make unclear or difficult to understand",
                 "The politician tried to obfuscate the real issue."),
            ],
        }


# Singleton
_english_teacher = None

def get_english_teacher() -> EnglishTeacher:
    """Get the English teacher singleton."""
    global _english_teacher
    if _english_teacher is None:
        _english_teacher = EnglishTeacher()
    return _english_teacher
