"""
STT Language Model Enhancement
Integrates KenLM n-gram language model with wav2vec2 for context-aware corrections
"""
import sys
import os
from pathlib import Path

# KenLM is installed via pip (pypi-kenlm package)
# No need for path hacks - just import directly

import numpy as np
import torch
from typing import Optional, List, Tuple
import json

# KenLM for n-gram language model - installed via pypi-kenlm
HAS_KENLM = False
try:
    import kenlm
    if hasattr(kenlm, 'Model'):
        HAS_KENLM = True
        print(f"[STT-LM] KenLM loaded successfully")
    else:
        print("[STT-LM] KenLM imported but Model class missing")
except ImportError as e:
    print(f"[STT-LM] KenLM not available ({e}) - using beam search without LM")

# pyctcdecode for CTC beam search with language model
try:
    from pyctcdecode import build_ctcdecoder
    HAS_PYCTCDECODE = True
except ImportError:
    HAS_PYCTCDECODE = False
    print("[STT-LM] pyctcdecode not available - install with: pip install pyctcdecode")


class LanguageModelDecoder:
    """
    Enhances wav2vec2 CTC output with KenLM language model.
    
    Benefits:
    - Context-aware corrections (fixes "sounds-like" errors)
    - Better word boundaries
    - Improved accuracy on homophones (there/their/they're)
    - Handles out-of-vocabulary words better
    """
    
    def __init__(self, vocab_path: Optional[Path] = None, lm_path: Optional[Path] = None):
        """
        Initialize language model decoder.
        
        Args:
            vocab_path: Path to vocabulary file (vocab.json from wav2vec2)
            lm_path: Path to KenLM .arpa or .bin file
        """
        self.vocab_path = vocab_path
        self.lm_path = lm_path
        self.decoder = None
        self.vocab = None
        
        # Check dependencies - pyctcdecode is required, KenLM is optional
        if not HAS_PYCTCDECODE:
            print("[STT-LM] pyctcdecode not available - using greedy decoding")
            return
        
        # KenLM is optional - beam search still works without it
        if not HAS_KENLM:
            print("[STT-LM] KenLM not available - will use beam search without language model")
        
        # Load vocabulary
        if vocab_path and vocab_path.exists():
            self._load_vocabulary(vocab_path)
        else:
            print("[STT-LM] No vocabulary provided - will use default")
        
        # Load language model - prefer explicit path, then models/english_lm.bin, then english_3gram.bin
        if lm_path and lm_path.exists():
            self._load_language_model(lm_path)
        else:
            project_root = Path(__file__).parent.parent.parent.parent
            preferred_lm = project_root / "models" / "english_lm.bin"
            legacy_lm = project_root / "english_3gram.bin"
            if preferred_lm.exists():
                print(f"[STT-LM] Found language model: {preferred_lm}")
                self._load_language_model(preferred_lm)
            elif legacy_lm.exists():
                print(f"[STT-LM] Found trained language model: {legacy_lm}")
                self._load_language_model(legacy_lm)
            else:
                print("[STT-LM] No language model found - will download default")
                self._download_default_lm()
    
    def _get_comprehensive_unigrams(self) -> List[str]:
        """
        Get comprehensive word list for beam search word segmentation.
        This is CRITICAL for proper word boundaries in character-level CTC.
        """
        # Most common English words + Monica-specific vocabulary
        # This helps the decoder properly segment words
        return [
            # Articles, prepositions, conjunctions
            "the", "a", "an", "and", "or", "but", "if", "then", "else", "when",
            "where", "why", "how", "what", "which", "who", "whom", "whose",
            "in", "on", "at", "to", "for", "of", "with", "by", "from", "up",
            "about", "into", "through", "during", "before", "after", "above",
            "below", "between", "under", "again", "further", "once", "here",
            "there", "all", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "also", "now", "out", "over", "off",
            # Pronouns
            "i", "me", "my", "mine", "myself",
            "you", "your", "yours", "yourself",
            "he", "him", "his", "himself",
            "she", "her", "hers", "herself",
            "it", "its", "itself",
            "we", "us", "our", "ours", "ourselves",
            "they", "them", "their", "theirs", "themselves",
            "this", "that", "these", "those",
            # Common verbs
            "is", "are", "was", "were", "be", "been", "being", "am",
            "have", "has", "had", "having",
            "do", "does", "did", "doing", "done",
            "will", "would", "could", "should", "can", "may", "might", "must",
            "shall", "need", "dare", "ought",
            "go", "going", "goes", "went", "gone",
            "get", "gets", "got", "getting",
            "make", "makes", "made", "making",
            "know", "knows", "knew", "known", "knowing",
            "think", "thinks", "thought", "thinking",
            "take", "takes", "took", "taken", "taking",
            "see", "sees", "saw", "seen", "seeing",
            "come", "comes", "came", "coming",
            "want", "wants", "wanted", "wanting",
            "look", "looks", "looked", "looking",
            "use", "uses", "used", "using",
            "find", "finds", "found", "finding",
            "give", "gives", "gave", "given", "giving",
            "tell", "tells", "told", "telling",
            "say", "says", "said", "saying",
            "ask", "asks", "asked", "asking",
            "work", "works", "worked", "working",
            "seem", "seems", "seemed", "seeming",
            "feel", "feels", "felt", "feeling",
            "try", "tries", "tried", "trying",
            "leave", "leaves", "left", "leaving",
            "call", "calls", "called", "calling",
            "keep", "keeps", "kept", "keeping",
            "let", "lets", "letting",
            "begin", "begins", "began", "begun", "beginning",
            "show", "shows", "showed", "shown", "showing",
            "hear", "hears", "heard", "hearing",
            "play", "plays", "played", "playing",
            "run", "runs", "ran", "running",
            "move", "moves", "moved", "moving",
            "live", "lives", "lived", "living",
            "believe", "believes", "believed", "believing",
            "hold", "holds", "held", "holding",
            "bring", "brings", "brought", "bringing",
            "happen", "happens", "happened", "happening",
            "write", "writes", "wrote", "written", "writing",
            "provide", "provides", "provided", "providing",
            "sit", "sits", "sat", "sitting",
            "stand", "stands", "stood", "standing",
            "lose", "loses", "lost", "losing",
            "pay", "pays", "paid", "paying",
            "meet", "meets", "met", "meeting",
            "include", "includes", "included", "including",
            "continue", "continues", "continued", "continuing",
            "set", "sets", "setting",
            "learn", "learns", "learned", "learning",
            "change", "changes", "changed", "changing",
            "lead", "leads", "led", "leading",
            "understand", "understands", "understood", "understanding",
            "watch", "watches", "watched", "watching",
            "follow", "follows", "followed", "following",
            "stop", "stops", "stopped", "stopping",
            "create", "creates", "created", "creating",
            "speak", "speaks", "spoke", "spoken", "speaking",
            "read", "reads", "reading",
            "spend", "spends", "spent", "spending",
            "grow", "grows", "grew", "grown", "growing",
            "open", "opens", "opened", "opening",
            "walk", "walks", "walked", "walking",
            "win", "wins", "won", "winning",
            "offer", "offers", "offered", "offering",
            "remember", "remembers", "remembered", "remembering",
            "love", "loves", "loved", "loving",
            "consider", "considers", "considered", "considering",
            "appear", "appears", "appeared", "appearing",
            "buy", "buys", "bought", "buying",
            "wait", "waits", "waited", "waiting",
            "serve", "serves", "served", "serving",
            "die", "dies", "died", "dying",
            "send", "sends", "sent", "sending",
            "expect", "expects", "expected", "expecting",
            "build", "builds", "built", "building",
            "stay", "stays", "stayed", "staying",
            "fall", "falls", "fell", "fallen", "falling",
            "cut", "cuts", "cutting",
            "reach", "reaches", "reached", "reaching",
            "kill", "kills", "killed", "killing",
            "remain", "remains", "remained", "remaining",
            # Common nouns
            "time", "year", "people", "way", "day", "man", "thing", "woman",
            "life", "child", "world", "school", "state", "family", "student",
            "group", "country", "problem", "hand", "part", "place", "case",
            "week", "company", "system", "program", "question", "work", "government",
            "number", "night", "point", "home", "water", "room", "mother", "area",
            "money", "story", "fact", "month", "lot", "right", "study", "book",
            "eye", "job", "word", "business", "issue", "side", "kind", "head",
            "house", "service", "friend", "father", "power", "hour", "game", "line",
            "end", "member", "law", "car", "city", "community", "name", "president",
            "team", "minute", "idea", "kid", "body", "information", "back", "parent",
            "face", "others", "level", "office", "door", "health", "person", "art",
            "war", "history", "party", "result", "change", "morning", "reason", "research",
            "girl", "guy", "moment", "air", "teacher", "force", "education",
            # Common adjectives
            "good", "new", "first", "last", "long", "great", "little", "own",
            "other", "old", "right", "big", "high", "different", "small", "large",
            "next", "early", "young", "important", "few", "public", "bad", "same",
            "able", "human", "local", "sure", "free", "better", "true", "whole",
            "special", "hard", "best", "possible", "full", "clear", "political",
            "real", "past", "recent", "certain", "personal", "open", "red", "difficult",
            "available", "likely", "short", "single", "medical", "current", "wrong",
            "private", "low", "military", "white", "close", "necessary", "late",
            "various", "international", "fine", "economic", "easy", "strong", "nice",
            # Common adverbs
            "up", "so", "out", "just", "now", "how", "then", "more", "also",
            "here", "well", "only", "very", "even", "back", "there", "down",
            "still", "in", "as", "too", "when", "never", "really", "most",
            "today", "way", "always", "much", "right", "again", "once", "later",
            # Numbers and quantities
            "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
            "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty",
            "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion",
            "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
            "ninth", "tenth", "half", "quarter", "dozen", "couple", "several", "multiple",
            # Time words
            "today", "tomorrow", "yesterday", "morning", "afternoon", "evening", "night",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "january", "february", "march", "april", "may", "june", "july",
            "august", "september", "october", "november", "december",
            # Monica-specific vocabulary
            "monica", "initialize", "initialise", "initialization", "hello", "hi", "hey",
            "yes", "no", "okay", "ok", "please", "thanks", "thank", "sorry",
            "help", "stop", "start", "pause", "resume", "quit", "exit",
            "date", "weather", "news", "search", "find", "show", "tell", "explain",
            "computer", "laptop", "phone", "screen", "window", "browser", "internet",
            "email", "message", "text", "call", "video", "audio", "music", "song",
            "picture", "photo", "image", "file", "folder", "document", "note",
            # Question words and phrases
            "what", "whats", "what's", "when", "where", "why", "how", "who",
            "which", "whose", "whom", "can", "could", "would", "should", "will",
            # CRITICAL: Words causing segmentation issues
            "birth", "birthday", "born", "earth", "mean", "meant", "said",
            "witch", "witches", "exist", "exists", "existed", "existence",
            "age", "old", "young", "baby", "child", "children", "kid", "kids",
            "myself", "yourself", "himself", "herself", "itself", "ourselves",
            "actually", "really", "probably", "maybe", "perhaps", "certainly",
            "always", "never", "sometimes", "often", "usually", "already",
            "about", "around", "through", "because", "without", "within",
            "another", "other", "others", "something", "anything", "nothing",
            "everything", "someone", "anyone", "everyone", "nobody", "everybody",
            "however", "whatever", "whenever", "wherever", "whichever", "whoever",
            "question", "answer", "problem", "solution", "reason", "example",
            "information", "knowledge", "understand", "understanding", "explain",
            "believe", "opinion", "fact", "truth", "idea", "thought", "mind",
            "remember", "forget", "learn", "teach", "study", "practice",
            "guess", "suppose", "assume", "wonder", "curious", "interesting",
            "important", "necessary", "possible", "impossible", "difficult", "easy",
            "simple", "complex", "different", "same", "similar", "special",
            "favorite", "beautiful", "wonderful", "amazing", "awesome", "great",
            "terrible", "horrible", "awful", "bad", "wrong", "right", "correct",
            "exactly", "completely", "totally", "absolutely", "definitely",
            "tomorrow", "yesterday", "tonight", "afternoon", "evening", "midnight",
            "year", "month", "week", "hour", "minute", "second", "moment",
            "birthday", "anniversary", "holiday", "vacation", "weekend",
            "family", "mother", "father", "brother", "sister", "son", "daughter",
            "husband", "wife", "friend", "friends", "people", "person",
            "world", "country", "city", "town", "place", "home", "house",
            "school", "work", "job", "office", "company", "business",
            "money", "price", "cost", "pay", "buy", "sell", "spend", "save",
            "food", "water", "drink", "eat", "breakfast", "lunch", "dinner",
            "movie", "show", "game", "play", "watch", "listen", "read", "write",
            "talk", "speak", "say", "said", "tell", "told", "ask", "asked",
            "love", "like", "hate", "want", "need", "hope", "wish", "prefer",
            "happy", "sad", "angry", "tired", "hungry", "thirsty", "sick",
            "better", "worse", "best", "worst", "more", "less", "most", "least",
            "enough", "many", "much", "few", "little", "lot", "lots", "plenty",
        ]
    
    def _load_vocabulary(self, vocab_path: Path):
        """Load vocabulary from wav2vec2 model."""
        try:
            with open(vocab_path, 'r', encoding='utf-8') as f:
                self.vocab = json.load(f)
            
            # Convert to list format for pyctcdecode
            # Following HuggingFace official approach: sort by index, convert to lowercase
            # Source: https://huggingface.co/blog/wav2vec2-with-ngram
            sorted_vocab_dict = {k.lower(): v for k, v in sorted(self.vocab.items(), key=lambda item: item[1])}
            
            # Extract just the keys in sorted order - this is what pyctcdecode expects
            self.vocab_list = list(sorted_vocab_dict.keys())
            
            print(f"[STT-LM] Loaded vocabulary: {len(self.vocab_list)} tokens")
            print(f"[STT-LM] Vocab sample: {self.vocab_list[:10]}")
            
        except Exception as e:
            print(f"[STT-LM] Error loading vocabulary: {e}")
            self.vocab = None
    
    def _load_language_model(self, lm_path: Path):
        """Load language model or create beam search decoder without LM."""
        try:
            if not HAS_PYCTCDECODE:
                return
            
            # Load comprehensive unigrams for proper word segmentation
            # This is CRITICAL for proper word boundaries with character-level CTC
            unigrams = self._get_comprehensive_unigrams()
            print(f"[STT-LM] Using {len(unigrams)} unigrams for word segmentation")
            
            if HAS_KENLM and lm_path and lm_path.exists():
                # Build CTC decoder WITH language model
                print(f"[STT-LM] Loading language model from {lm_path}")
                self.decoder = build_ctcdecoder(
                    labels=self.vocab_list,
                    kenlm_model_path=str(lm_path),
                    unigrams=unigrams,
                    alpha=0.5,  # Language model weight
                    beta=1.5,   # Word insertion bonus
                )
                print("[STT-LM] Language model decoder ready (with KenLM)")
            else:
                # Build CTC decoder WITHOUT language model - still uses beam search!
                print("[STT-LM] Building beam search decoder (without KenLM)")
                self.decoder = build_ctcdecoder(
                    labels=self.vocab_list,
                    unigrams=unigrams,  # Unigrams still help with word boundaries
                )
                print("[STT-LM] Beam search decoder ready (unigrams only)")
            
        except Exception as e:
            print(f"[STT-LM] Error building decoder: {e}")
            self.decoder = None
    
    def _download_default_lm(self):
        """Download default English language model or use beam search without LM."""
        try:
            if not HAS_PYCTCDECODE:
                return
            
            # If KenLM is available, try to download LM
            if HAS_KENLM:
                # Use LibriSpeech 4-gram model (commonly used with wav2vec2)
                print("[STT-LM] Downloading default English 4-gram language model...")
                print("[STT-LM] This may take a few minutes on first run...")
                
                lm_url = "https://www.openslr.org/resources/11/4-gram.arpa.gz"
                cache_dir = Path.home() / ".cache" / "monica_ai" / "language_models"
                cache_dir.mkdir(parents=True, exist_ok=True)
                lm_file = cache_dir / "librispeech_4gram.arpa"
                
                if not lm_file.exists():
                    import urllib.request
                    import gzip
                    import shutil
                    
                    print(f"[STT-LM] Downloading from {lm_url}...")
                    gz_file = cache_dir / "4-gram.arpa.gz"
                    urllib.request.urlretrieve(lm_url, gz_file)
                    
                    print("[STT-LM] Extracting...")
                    with gzip.open(gz_file, 'rb') as f_in:
                        with open(lm_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    gz_file.unlink()
                    print(f"[STT-LM] Language model saved to {lm_file}")
                
                self.lm_path = lm_file
                self._load_language_model(lm_file)
            else:
                # No KenLM - just use beam search with unigrams
                print("[STT-LM] KenLM not available - using beam search with unigrams only")
                self._load_language_model(None)
            
        except Exception as e:
            print(f"[STT-LM] Error: {e}")
            print("[STT-LM] Falling back to beam search without language model")
            self._load_language_model(None)
    
    def decode_with_lm(self, logits: np.ndarray) -> str:
        """
        Decode CTC logits with language model.
        
        Args:
            logits: CTC output logits [time_steps, vocab_size]
            
        Returns:
            Decoded text with language model corrections
        """
        if self.decoder is None:
            # Fallback to greedy decoding
            return self._greedy_decode(logits)
        
        try:
            # Beam search with language model
            text = self.decoder.decode(logits)
            return text
            
        except Exception as e:
            print(f"[STT-LM] Decoding error: {e}")
            return self._greedy_decode(logits)
    
    def decode_batch_with_lm(self, logits_batch: np.ndarray) -> List[str]:
        """
        Decode batch of CTC logits with language model.
        
        Args:
            logits_batch: Batch of CTC logits [batch, time_steps, vocab_size]
            
        Returns:
            List of decoded texts
        """
        if self.decoder is None:
            return [self._greedy_decode(logits) for logits in logits_batch]
        
        try:
            # Batch beam search
            texts = self.decoder.decode_batch(logits_batch)
            return texts
            
        except Exception as e:
            print(f"[STT-LM] Batch decoding error: {e}")
            return [self._greedy_decode(logits) for logits in logits_batch]
    
    def _greedy_decode(self, logits: np.ndarray) -> str:
        """Fallback greedy CTC decoding without language model."""
        # Get most likely token at each timestep
        predicted_ids = np.argmax(logits, axis=-1)
        
        # CTC collapse: remove repeated tokens and blanks
        decoded = []
        prev_id = None
        
        for token_id in predicted_ids:
            if token_id != prev_id and token_id != 0:  # 0 is typically blank
                if token_id < len(self.vocab_list):
                    token = self.vocab_list[token_id]
                    # Convert word delimiter | to space
                    if token == '|':
                        decoded.append(' ')
                    else:
                        decoded.append(token)
            prev_id = token_id
        
        result = ''.join(decoded).strip()
        # Clean up multiple spaces
        import re
        result = re.sub(r' +', ' ', result)
        return result
    
    def is_available(self) -> bool:
        """Check if language model decoder is available."""
        return self.decoder is not None


class LanguageModelCache:
    """Cache for language model to avoid reloading."""
    
    def __init__(self):
        self.decoder = None
        self.model_path = None
    
    def get_decoder(self, vocab_path: Path, lm_path: Optional[Path] = None) -> LanguageModelDecoder:
        """Get or create language model decoder."""
        # Check if we need to reload
        if self.decoder is None or self.model_path != lm_path:
            self.decoder = LanguageModelDecoder(vocab_path, lm_path)
            self.model_path = lm_path
        
        return self.decoder


# Global cache
_lm_cache = LanguageModelCache()


def get_language_model_decoder(vocab_path: Path, lm_path: Optional[Path] = None) -> LanguageModelDecoder:
    """
    Get language model decoder (cached).
    
    Args:
        vocab_path: Path to wav2vec2 vocabulary
        lm_path: Optional path to KenLM model
        
    Returns:
        LanguageModelDecoder instance
    """
    return _lm_cache.get_decoder(vocab_path, lm_path)


def enhance_wav2vec2_with_lm(model_dir: Path) -> bool:
    """
    Check if wav2vec2 model can be enhanced with language model.
    
    Args:
        model_dir: Path to wav2vec2 model directory
        
    Returns:
        True if enhancement is possible
    """
    vocab_file = model_dir / "vocab.json"
    
    if not vocab_file.exists():
        print("[STT-LM] No vocab.json found - cannot enhance with LM")
        return False
    
    if not HAS_KENLM or not HAS_PYCTCDECODE:
        print("[STT-LM] Missing dependencies for LM enhancement")
        print("[STT-LM] Install with: pip install pyctcdecode")
        print("[STT-LM] Install with: pip install https://github.com/kpu/kenlm/archive/master.zip")
        return False
    
    return True
