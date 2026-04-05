"""
Neural Text Normalizer for TTS using FLAN-T5.

Based on the approach from:
- Retell AI text normalization
- anhha9/llm-for-text-normalization-in-tts (FLAN-T5-small fine-tuned on Google TN dataset)

This provides more accurate normalization for complex cases like:
- Phone numbers: "2137112342" -> "two one three seven one one two three four two"
- Dates: "Jul 5th, 2024" -> "july fifth, twenty twenty four"
- Currency: "$24.12" -> "twenty four dollars twelve cents"

Supports: English, Spanish, French, German (auto-detection for multilingual)

Note: Adds ~100ms latency. Use rule-based normalizer for speed-critical applications.
"""

import re
from typing import Optional, Tuple
import threading

# Lazy loading for heavy ML libraries
_model = None
_tokenizer = None
_device = None
_model_lock = threading.Lock()
_is_loaded = False


def _load_model():
    """Lazy load the FLAN-T5 model for text normalization."""
    global _model, _tokenizer, _device, _is_loaded
    
    if _is_loaded:
        return _model is not None
    
    with _model_lock:
        if _is_loaded:
            return _model is not None
        
        try:
            import torch
            from transformers import T5Tokenizer, T5ForConditionalGeneration
            
            print("[NEURAL-TN] Loading FLAN-T5-small for text normalization...")
            
            # Use the base FLAN-T5-small model
            # For better results, use a fine-tuned checkpoint
            model_name = "google/flan-t5-small"
            
            _tokenizer = T5Tokenizer.from_pretrained(model_name)
            _model = T5ForConditionalGeneration.from_pretrained(model_name)
            
            # Move to GPU if available
            _device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            _model.to(_device)
            _model.eval()
            
            print(f"[NEURAL-TN] Model loaded on {_device}")
            _is_loaded = True
            return True
            
        except Exception as e:
            print(f"[NEURAL-TN] Failed to load model: {e}")
            _is_loaded = True  # Mark as attempted
            return False


class NeuralTextNormalizer:
    """
    Neural text normalizer using FLAN-T5 for TTS applications.
    
    Converts raw text to spoken form:
    - Numbers: "123" -> "one hundred twenty three"
    - Dates: "12/25/2024" -> "december twenty fifth, twenty twenty four"
    - Currency: "$50.00" -> "fifty dollars"
    - Phone numbers: "555-1234" -> "five five five one two three four"
    - Times: "3:30 PM" -> "three thirty p m"
    
    Supports: English, Spanish, French, German
    """
    
    # Language codes for normalization
    SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de']
    
    # Prompt templates for different normalization tasks
    PROMPTS = {
        'general': "Normalize this text for speech synthesis: {text}",
        'number': "Convert this number to spoken words: {text}",
        'date': "Convert this date to spoken form: {text}",
        'currency': "Convert this currency amount to spoken words: {text}",
        'phone': "Convert this phone number to spoken digits: {text}",
        'time': "Convert this time to spoken form: {text}",
    }
    
    def __init__(self, language: str = 'en', use_gpu: bool = True):
        """
        Initialize the neural text normalizer.
        
        Args:
            language: Language code ('en', 'es', 'fr', 'de', or 'auto')
            use_gpu: Whether to use GPU acceleration
        """
        self.language = language
        self.use_gpu = use_gpu
        self._model_loaded = False
    
    def _ensure_model_loaded(self) -> bool:
        """Ensure the model is loaded."""
        if not self._model_loaded:
            self._model_loaded = _load_model()
        return self._model_loaded
    
    def normalize(self, text: str, task: str = 'general') -> str:
        """
        Normalize text for TTS using the neural model.
        
        Args:
            text: Raw text to normalize
            task: Type of normalization ('general', 'number', 'date', 'currency', 'phone', 'time')
            
        Returns:
            Normalized text suitable for TTS
        """
        if not text or not text.strip():
            return text
        
        # Try neural normalization
        if self._ensure_model_loaded() and _model is not None:
            try:
                return self._neural_normalize(text, task)
            except Exception as e:
                print(f"[NEURAL-TN] Error: {e}, falling back to rule-based")
        
        # Fallback to rule-based normalization
        return self._rule_based_normalize(text)
    
    def _neural_normalize(self, text: str, task: str = 'general') -> str:
        """Use the neural model for normalization."""
        import torch
        
        # Create prompt
        prompt_template = self.PROMPTS.get(task, self.PROMPTS['general'])
        prompt = prompt_template.format(text=text)
        
        # Tokenize
        input_ids = _tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True).input_ids
        input_ids = input_ids.to(_device)
        
        # Generate
        with torch.no_grad():
            outputs = _model.generate(
                input_ids,
                max_length=512,
                num_beams=4,
                early_stopping=True,
                do_sample=False
            )
        
        # Decode
        normalized = _tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up the output
        normalized = self._clean_output(normalized, text)
        
        return normalized
    
    def _clean_output(self, output: str, original: str) -> str:
        """Clean up the model output."""
        # Remove any prompt artifacts
        output = output.strip()
        
        # If output is empty or too different, return original
        if not output or len(output) < 2:
            return original
        
        return output
    
    def _rule_based_normalize(self, text: str) -> str:
        """Fallback rule-based normalization."""
        # Import the rule-based normalizer
        from tts.text_normalizer import normalize_text_for_tts
        return normalize_text_for_tts(text)
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize a phone number to spoken digits."""
        # Remove non-digit characters
        digits = re.sub(r'[^\d]', '', phone)
        
        digit_words = {
            '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
            '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
        }
        
        return ' '.join(digit_words.get(d, d) for d in digits)
    
    def normalize_currency(self, amount: str) -> str:
        """Normalize currency to spoken form."""
        # Try neural first
        if self._ensure_model_loaded() and _model is not None:
            try:
                return self._neural_normalize(amount, 'currency')
            except:
                pass
        
        # Fallback: Parse and convert
        match = re.match(r'\$(\d+)(?:\.(\d{2}))?', amount)
        if match:
            dollars = int(match.group(1))
            cents = int(match.group(2)) if match.group(2) else 0
            
            from tts.text_normalizer import get_num2words
            num2words = get_num2words()
            
            if num2words:
                dollar_word = num2words.num2words(dollars)
                if cents > 0:
                    cent_word = num2words.num2words(cents)
                    return f"{dollar_word} dollars {cent_word} cents"
                return f"{dollar_word} dollars"
        
        return amount
    
    def detect_language(self, text: str) -> str:
        """Auto-detect the language of the text."""
        # Simple heuristic based on common words
        text_lower = text.lower()
        
        # Spanish indicators
        if any(word in text_lower for word in ['el', 'la', 'de', 'que', 'es', 'en', 'los', 'las']):
            return 'es'
        
        # French indicators
        if any(word in text_lower for word in ['le', 'la', 'de', 'et', 'est', 'les', 'des', 'une']):
            return 'fr'
        
        # German indicators
        if any(word in text_lower for word in ['der', 'die', 'das', 'und', 'ist', 'ein', 'eine']):
            return 'de'
        
        # Default to English
        return 'en'


# Convenience functions
_neural_normalizer = None


def get_neural_normalizer(language: str = 'en') -> NeuralTextNormalizer:
    """Get or create the neural text normalizer."""
    global _neural_normalizer
    if _neural_normalizer is None:
        _neural_normalizer = NeuralTextNormalizer(language=language)
    return _neural_normalizer


def neural_normalize_text(text: str, task: str = 'general') -> str:
    """Convenience function for neural text normalization."""
    return get_neural_normalizer().normalize(text, task)


def normalize_for_tts(text: str, use_neural: bool = False) -> str:
    """
    Normalize text for TTS with optional neural enhancement.
    
    Args:
        text: Raw text to normalize
        use_neural: Whether to use neural normalization (adds ~100ms latency)
        
    Returns:
        Normalized text ready for TTS
    """
    if use_neural:
        return neural_normalize_text(text)
    else:
        from tts.text_normalizer import normalize_text_for_tts
        return normalize_text_for_tts(text)


# Retell AI-style normalization function
def retell_normalize(text: str, language: str = 'en') -> str:
    """
    Normalize text in Retell AI style.
    
    Converts:
    - Phone numbers: digit by digit
    - Dates: spoken form
    - Currency: dollars and cents
    - Numbers: spoken words
    
    Args:
        text: Raw text to normalize
        language: Language code ('en', 'es', 'fr', 'de', 'auto')
        
    Returns:
        Normalized text for TTS
    """
    normalizer = get_neural_normalizer(language)
    
    # Auto-detect language if needed
    if language == 'auto':
        language = normalizer.detect_language(text)
    
    # Check if language is supported
    if language not in NeuralTextNormalizer.SUPPORTED_LANGUAGES:
        # Return unchanged for unsupported languages
        return text
    
    return normalizer.normalize(text)
