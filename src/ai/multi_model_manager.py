"""
Multi-Model Cognitive System for Monica AI
Integrates multiple free AI models to work in cohesion
"""
import threading
import queue
import time
from typing import List, Dict, Optional, Callable, Tuple
from dataclasses import dataclass
import json
import ollama
import re

@dataclass
class ModelCapability:
    """Defines what each model is good at."""
    name: str
    size: str
    strengths: List[str]
    speed: str  # fast, medium, slow
    context_length: int
    instruction_following: int  # 1-5 rating
    
class MultiModelManager:
    """
    Manages multiple AI models working together for Monica.
    All models are completely FREE from Ollama.
    """
    
    def __init__(self):
        """Initialize the multi-model system."""
        self.models = self._define_models()
        self.active_models = set()
        self._check_available_models()
        
    def _define_models(self) -> Dict[str, ModelCapability]:
        """Define all free models and their capabilities - ENGLISH ONLY MODELS."""
        return {
            # === FAST MODELS (< 1 second response) ===
            
            # StableLM 2 - FASTEST, good for simple queries
            "stablelm2": ModelCapability(
                name="StableLM 2",
                size="1.6B",
                strengths=["quick_response", "simple_queries", "chat"],
                speed="fastest",
                context_length=4096,
                instruction_following=3
            ),
            
            # SmolLM 2 - Very fast, good quality for size
            "smollm2": ModelCapability(
                name="SmolLM 2",
                size="1.7B",
                strengths=["quick_response", "efficiency", "general"],
                speed="fastest",
                context_length=8192,
                instruction_following=3
            ),
            
            # === BALANCED MODELS (1-3 second response) ===
            
            # Llama 3.2 - Best balance of speed and quality
            "llama3.2": ModelCapability(
                name="Llama 3.2",
                size="3B",
                strengths=["general", "instruction_following", "conversation"],
                speed="fast",
                context_length=8192,
                instruction_following=4
            ),
            
            # Granite 3.1 MoE - IBM's model, good reasoning
            "granite3.1-moe": ModelCapability(
                name="Granite 3.1 MoE",
                size="3B",
                strengths=["reasoning", "analysis", "factual"],
                speed="fast",
                context_length=8192,
                instruction_following=4
            ),
            
            # Phi 3 Mini - Microsoft, good for technical
            "phi3:mini": ModelCapability(
                name="Phi 3 Mini",
                size="3.8B",
                strengths=["technical", "code", "reasoning"],
                speed="fast",
                context_length=4096,
                instruction_following=4
            ),
            
            # === HIGH QUALITY MODELS (3-5 second response) ===
            
            # Mistral Nemo - Best quality, long context
            "mistral-nemo": ModelCapability(
                name="Mistral Nemo",
                size="12B",
                strengths=["quality", "long_context", "complex_reasoning"],
                speed="medium",
                context_length=128000,
                instruction_following=5
            ),
            
            # Instruction specialist
            "hermes3": ModelCapability(
                name="Hermes 3",
                size="8B",
                strengths=["instruction_following", "tasks", "structured_output"],
                speed="medium",
                context_length=8192,
                instruction_following=5
            ),
            
            # Creative and empathetic
            "dolphin-mistral": ModelCapability(
                name="Dolphin Mistral",
                size="7B",
                strengths=["creative", "empathy", "conversation"],
                speed="medium",
                context_length=16384,
                instruction_following=4
            ),
            
            # Vision understanding (if camera active)
            "llava": ModelCapability(
                name="LLaVA",
                size="7B",
                strengths=["vision", "image_understanding", "description"],
                speed="slow",
                context_length=4096,
                instruction_following=3
            ),
            
            # Code specialist
            "qwen2.5-coder": ModelCapability(
                name="Qwen Coder",
                size="7B",
                strengths=["code", "debugging", "programming"],
                speed="medium",
                context_length=32768,
                instruction_following=4
            )
        }
    
    def _check_available_models(self):
        """Check which models are installed."""
        try:
            result = ollama.list()
            installed = [m.get('name', '') for m in result.get('models', [])]
            for model in self.models:
                if any(model.startswith(ins.split(':')[0]) for ins in installed if ins):
                    self.active_models.add(model)
                    print(f"[*] Model available: {model}")
            
            # If no models found but ollama is working, assume common models are available
            if not self.active_models:
                # Try to check if llama3.2 is available by attempting a simple call
                try:
                    ollama.show('llama3.2')
                    self.active_models.add('llama3.2')
                    print("[*] Model available: llama3.2 (detected via show)")
                except:
                    pass
        except Exception as e:
            print(f"[AI] Could not check models: {e}")
    
    def install_missing_models(self, callback: Optional[Callable] = None):
        """Install all missing models for full capability."""
        missing = set(self.models.keys()) - self.active_models
        for model in missing:
            if callback:
                callback(f"Installing {model}...")
            try:
                ollama.pull(model)
                self.active_models.add(model)
                if callback:
                    callback(f"[*] Installed {model}")
            except Exception as e:
                if callback:
                    callback(f"[*] Failed to install {model}: {e}")
    
    def analyze_query(self, text: str) -> Dict[str, any]:
        """Analyze query to determine best model strategy."""
        text_lower = text.lower()
        
        analysis = {
            "needs_speed": len(text.split()) < 10 and any(
                word in text_lower for word in ["what time", "what date", "weather", "quick"]
            ),
            "needs_reasoning": any(
                word in text_lower for word in ["explain", "why", "how", "understand", "think"]
            ),
            "needs_creativity": any(
                word in text_lower for word in ["story", "poem", "imagine", "create", "write"]
            ),
            "needs_code": any(
                word in text_lower for word in ["code", "program", "function", "debug", "python", "javascript"]
            ),
            "needs_vision": any(
                word in text_lower for word in ["look", "see", "image", "picture", "photo", "show me"]
            ),
            "needs_empathy": any(
                word in text_lower for word in ["feel", "sad", "happy", "worried", "scared", "help me"]
            ),
            "is_instruction": text_lower.startswith(("do", "make", "create", "write", "generate")),
            "complexity": "simple" if len(text.split()) < 20 else "complex"
        }
        
        return analysis
    
    def select_models(self, analysis: Dict) -> List[str]:
        """
        Smart Model Routing System (OPTIMIZED FOR 8GB VRAM):
        - LLAMA3.2: Primary model for all tasks (2GB, fits in GPU)
        - PHI3:MINI: Technical/reasoning (2.2GB)
        - STABLELM2/SMOLLM2: Ultra-fast for simple commands (<2GB)
        
        NOTE: Larger models (mistral-nemo 7GB, qwen2.5 4.7GB) are too slow
        on 8GB VRAM because they run partially on CPU.
        """
        
        # === ULTRA-FAST PATH: Simple commands (< 1 second) ===
        if analysis["needs_speed"]:
            if "stablelm2" in self.active_models:
                return ["stablelm2"]
            elif "smollm2" in self.active_models:
                return ["smollm2"]
            elif "llama3.2" in self.active_models:
                return ["llama3.2"]
        
        # === CODE/MATH PATH: Phi3 is good and fits in VRAM ===
        if analysis["needs_code"]:
            if "phi3:mini" in self.active_models:
                return ["phi3:mini"]
            elif "llama3.2" in self.active_models:
                return ["llama3.2"]
        
        # === REASONING/ANALYSIS PATH: Phi3 or Granite ===
        if analysis["needs_reasoning"]:
            if "phi3:mini" in self.active_models:
                return ["phi3:mini"]
            elif "granite3.1-moe" in self.active_models:
                return ["granite3.1-moe"]
            elif "llama3.2" in self.active_models:
                return ["llama3.2"]
        
        # === CREATIVE/EMPATHY/GENERAL: Llama3.2 (fast and good quality) ===
        if "llama3.2" in self.active_models:
            return ["llama3.2"]
        
        # === FALLBACK: Any available fast model ===
        if "stablelm2" in self.active_models:
            return ["stablelm2"]
        elif "smollm2" in self.active_models:
            return ["smollm2"]
        elif "phi3:mini" in self.active_models:
            return ["phi3:mini"]
        elif self.active_models:
            return [list(self.active_models)[0]]
        
        return ["llama3.2"]  # Ultimate fallback
    
    def generate_ensemble(self, prompt: str, models: List[str], system_prompt: str = "") -> str:
        """
        Generate response using ensemble of models.
        Combines outputs for better quality.
        """
        responses = {}
        threads = []
        
        def query_model(model_name: str, result_dict: Dict):
            """Query a single model."""
            try:
                response = ollama.generate(
                    model=model_name,
                    prompt=prompt,
                    system=system_prompt,
                    options={
                        'temperature': 0.7,
                        'num_predict': 150  # Keep responses concise
                    }
                )
                result_dict[model_name] = response['response']
            except Exception as e:
                print(f"Error with {model_name}: {e}")
                result_dict[model_name] = None
        
        # Query all models in parallel
        for model in models[:3]:  # Limit to 3 models max for speed
            thread = threading.Thread(target=query_model, args=(model, responses))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete (with timeout)
        for thread in threads:
            thread.join(timeout=10)
        
        # Combine responses intelligently
        return self._combine_responses(responses, models)
    
    def _combine_responses(self, responses: Dict[str, str], models: List[str]) -> str:
        """Intelligently combine multiple model responses."""
        valid_responses = [r for r in responses.values() if r]
        
        if not valid_responses:
            return "I'm having trouble processing that request."
        
        if len(valid_responses) == 1:
            return valid_responses[0]
        
        # For multiple responses, pick the best one based on criteria
        best_response = None
        best_score = -1
        
        for model, response in responses.items():
            if not response:
                continue
                
            score = 0
            # Score based on model capability
            model_cap = self.models.get(model)
            if model_cap:
                score += model_cap.instruction_following
            
            # Prefer concise responses
            if 10 < len(response.split()) < 100:
                score += 2
            
            # Check for completeness (ends with punctuation)
            if response.strip()[-1] in '.!?':
                score += 1
            
            # Penalize repetition
            words = response.lower().split()
            if len(words) != len(set(words)):
                score -= 1
            
            if score > best_score:
                best_score = score
                best_response = response
        
        return best_response or valid_responses[0]
    
    def generate_chain_of_thought(self, prompt: str, models: List[str]) -> str:
        """
        Use models in sequence, each building on the previous.
        Great for complex reasoning.
        """
        current_context = prompt
        final_response = ""
        
        for i, model in enumerate(models):
            try:
                # Each model adds to the thinking
                if i == 0:
                    system = "You are Monica. Analyze this request and identify key points."
                elif i == len(models) - 1:
                    system = "You are Monica. Based on the analysis, provide a clear, concise answer."
                else:
                    system = "You are Monica. Expand on the previous analysis."
                
                response = ollama.generate(
                    model=model,
                    prompt=current_context,
                    system=system,
                    options={
                        'temperature': 0.7,
                        'num_predict': 150
                    }
                )
                
                result = response['response']
                if i == len(models) - 1:
                    final_response = result
                else:
                    current_context += f"\n\nAnalysis: {result}"
                    
            except Exception as e:
                print(f"Chain error with {model}: {e}")
                continue
        
        return final_response or "I need to think about that more."
    
    def get_status(self) -> Dict:
        """Get status of multi-model system."""
        return {
            "total_models": len(self.models),
            "active_models": len(self.active_models),
            "models": list(self.active_models),
            "capabilities": self._get_combined_capabilities()
        }
    
    def _get_combined_capabilities(self) -> List[str]:
        """Get all capabilities from active models."""
        capabilities = set()
        for model in self.active_models:
            if model in self.models:
                capabilities.update(self.models[model].strengths)
        return list(capabilities)

# Global instance
_multi_model_manager = None

def get_multi_model_manager():
    """Get or create the multi-model manager."""
    global _multi_model_manager
    if _multi_model_manager is None:
        _multi_model_manager = MultiModelManager()
    return _multi_model_manager
