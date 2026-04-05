"""
STT LLM Post-Processor
Uses GRMR-V3 specialized grammar model to clean up raw STT output
Fixes: punctuation, capitalization, grammar, formatting
"""
import re
from typing import Optional, Dict, List
from pathlib import Path
import json

# Try to import Ollama for local LLM
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    print("[STT-LLM] Ollama not available - install with: pip install ollama")

# Alternative: Try transformers for local models
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class STTPostProcessor:
    """
    Post-processes raw STT output using LLM for cleanup.
    
    Benefits:
    - Adds proper punctuation
    - Fixes capitalization
    - Corrects grammar errors
    - Formats numbers and dates
    - No STT retraining needed
    """
    
    def __init__(self, model_name: str = "qingy2024/GRMR-V3-Q1.7B", use_ollama: bool = False):
        """
        Initialize STT post-processor.
        
        Args:
            model_name: LLM model to use
                - "qingy2024/GRMR-V3-Q1.7B" (HuggingFace, 1.7B, FAST, specialized for grammar)
                - "qingy2024/GRMR-V3-Q3B" (HuggingFace, 3B, better quality)
                - "llama3.2:1b" (Ollama, 1B params, slower)
                - "phi3:mini" (Ollama, 3.8B params, good balance)
            use_ollama: Use Ollama (True) or HuggingFace (False)
                       Default False to use faster GRMR models
        """
        self.model_name = model_name
        self.use_ollama = use_ollama
        self.model = None
        self.tokenizer = None
        self.is_grmr_model = "GRMR" in model_name.upper()
        
        # System prompt for cleanup
        self.system_prompt = """You are a text cleanup assistant. Your job is to take raw speech-to-text output and clean it up by:
1. Adding proper punctuation (periods, commas, question marks, etc.)
2. Fixing capitalization (start of sentences, proper nouns)
3. Correcting obvious grammar errors
4. Formatting numbers and dates properly
5. Removing filler words if excessive (um, uh, like)

IMPORTANT: 
- Keep the original meaning and words
- Only fix formatting, punctuation, and obvious errors
- Do NOT add or remove content
- Do NOT rephrase or rewrite
- Output ONLY the cleaned text, no explanations

Example:
Input: "hey monica what time is it i need to know because i have a meeting at three thirty"
Output: "Hey Monica, what time is it? I need to know because I have a meeting at 3:30."
"""
        
        # Initialize model
        if use_ollama and HAS_OLLAMA:
            self._init_ollama()
        elif HAS_TRANSFORMERS:
            self._init_transformers()
        else:
            print("[STT-LLM] No LLM backend available")
            print("[STT-LLM] Install Ollama: https://ollama.ai/")
            print("[STT-LLM] Or install transformers: pip install transformers torch")
    
    def _init_ollama(self):
        """Initialize Ollama backend."""
        try:
            # Check if Ollama is running
            models = ollama.list()
            print(f"[STT-LLM] Ollama available with {len(models.get('models', []))} models")
            
            # Check if our model is available
            model_available = any(m['name'].startswith(self.model_name) for m in models.get('models', []))
            
            if not model_available:
                print(f"[STT-LLM] Model {self.model_name} not found")
                print(f"[STT-LLM] Pull with: ollama pull {self.model_name}")
                print("[STT-LLM] Note: GRMR-V3 (HuggingFace) is recommended over Ollama")
            else:
                print(f"[STT-LLM] Using Ollama model: {self.model_name}")
                self.model = "ollama"
            
        except Exception as e:
            print(f"[STT-LLM] Ollama initialization error: {e}")
            print("[STT-LLM] Make sure Ollama is running: ollama serve")
    
    def _init_transformers(self):
        """Initialize HuggingFace transformers backend."""
        try:
            print(f"[STT-LLM] Loading model {self.model_name} via transformers...")
            
            # Use GRMR models for best speed/quality on grammar correction
            if self.is_grmr_model:
                model_id = self.model_name
            elif "llama" in self.model_name.lower():
                model_id = "meta-llama/Llama-3.2-1B-Instruct"
            elif "phi" in self.model_name.lower():
                model_id = "microsoft/phi-2"
            else:
                model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            
            print(f"[STT-LLM] Model loaded: {model_id}")
            print(f"[STT-LLM] Using {'GRMR specialized' if self.is_grmr_model else 'general'} grammar correction")
            
        except Exception as e:
            print(f"[STT-LLM] Transformers initialization error: {e}")
            self.model = None
    
    def cleanup_transcription(self, raw_text: str, context: Optional[str] = None) -> str:
        """
        Clean up raw STT transcription using LLM.
        
        Args:
            raw_text: Raw transcription from STT
            context: Optional context (previous conversation, etc.)
            
        Returns:
            Cleaned up text with proper punctuation and formatting
        """
        if not raw_text or not raw_text.strip():
            return raw_text
        
        # Quick check: if already well-formatted, skip LLM
        if self._is_well_formatted(raw_text):
            return raw_text
        
        # Use LLM for cleanup
        if self.model == "ollama" and HAS_OLLAMA:
            return self._cleanup_with_ollama(raw_text, context)
        elif self.model and HAS_TRANSFORMERS:
            return self._cleanup_with_transformers(raw_text, context)
        else:
            # Fallback: basic rule-based cleanup
            return self._basic_cleanup(raw_text)
    
    def _is_well_formatted(self, text: str) -> bool:
        """Check if text is already well-formatted."""
        # Has punctuation
        has_punctuation = any(p in text for p in '.!?,;:')
        
        # Has capitalization
        has_capitals = any(c.isupper() for c in text)
        
        # Not too short
        long_enough = len(text.split()) > 3
        
        return has_punctuation and has_capitals and long_enough
    
    def _cleanup_with_ollama(self, raw_text: str, context: Optional[str] = None) -> str:
        """Cleanup using Ollama."""
        try:
            # Build prompt
            user_prompt = f"Clean up this speech-to-text output:\n\n{raw_text}"
            
            if context:
                user_prompt = f"Context: {context}\n\n{user_prompt}"
            
            # Call Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,  # Low temperature for consistent cleanup
                    "num_predict": 200,  # Limit output length
                }
            )
            
            cleaned = response['message']['content'].strip()
            
            # Validate output
            if not cleaned or len(cleaned) < len(raw_text) * 0.5:
                print("[STT-LLM] LLM output too short, using fallback")
                return self._basic_cleanup(raw_text)
            
            return cleaned
            
        except Exception as e:
            print(f"[STT-LLM] Ollama cleanup error: {e}")
            return self._basic_cleanup(raw_text)
    
    def _cleanup_with_transformers(self, raw_text: str, context: Optional[str] = None) -> str:
        """Cleanup using HuggingFace transformers."""
        try:
            # GRMR models use special chat template
            if self.is_grmr_model:
                messages = [{"role": "user", "content": raw_text}]
                prompt = self.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
            else:
                # Standard prompt for other models
                prompt = f"{self.system_prompt}\n\nInput: {raw_text}\nOutput:"
            
            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generate (GRMR models work best with temperature 0.7)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512 if self.is_grmr_model else 200,
                temperature=0.7 if self.is_grmr_model else 0.1,
                do_sample=True if self.is_grmr_model else False,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode
            full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract cleaned text
            if self.is_grmr_model:
                # GRMR outputs the corrected text directly after the prompt
                # Remove the input prompt to get just the correction
                if prompt in full_output:
                    cleaned = full_output.replace(prompt, "").strip()
                else:
                    cleaned = full_output.strip()
            else:
                # Extract after "Output:"
                if "Output:" in full_output:
                    cleaned = full_output.split("Output:")[-1].strip()
                else:
                    cleaned = full_output.strip()
            
            # Validate
            if not cleaned or len(cleaned) < len(raw_text) * 0.5:
                return self._basic_cleanup(raw_text)
            
            return cleaned
            
        except Exception as e:
            print(f"[STT-LLM] Transformers cleanup error: {e}")
            return self._basic_cleanup(raw_text)
    
    def _basic_cleanup(self, text: str) -> str:
        """Fallback rule-based cleanup without LLM."""
        # Capitalize first letter
        text = text[0].upper() + text[1:] if text else text
        
        # Add period at end if missing
        if text and text[-1] not in '.!?':
            text += '.'
        
        # Capitalize after sentence endings
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        # Fix common contractions
        text = text.replace(" dont ", " don't ")
        text = text.replace(" cant ", " can't ")
        text = text.replace(" wont ", " won't ")
        text = text.replace(" im ", " I'm ")
        text = text.replace(" youre ", " you're ")
        
        # Capitalize "I"
        text = re.sub(r'\bi\b', 'I', text)
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def is_available(self) -> bool:
        """Check if LLM post-processor is available."""
        return self.model is not None


# Global instance
_post_processor = None


def get_stt_post_processor(model_name: str = "qingy2024/GRMR-V3-Q1.7B") -> STTPostProcessor:
    """
    Get STT post-processor (cached).
    
    Args:
        model_name: LLM model to use
                   Default: GRMR-V3-Q1.7B (fast, specialized for grammar)
        
    Returns:
        STTPostProcessor instance
    """
    global _post_processor
    if _post_processor is None:
        _post_processor = STTPostProcessor(model_name, use_ollama=False)
    return _post_processor
