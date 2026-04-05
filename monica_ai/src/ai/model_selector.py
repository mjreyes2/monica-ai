"""
Model Selector for Monica AI
Selects the best model based on task type
"""

class ModelSelector:
    """Select optimal model for different tasks."""
    
    # Model specializations - ENGLISH ONLY MODELS
    MODELS = {
        # General conversation - use llama3.2 (English only)
        "general": "llama3.2",
        
        # Complex reasoning
        "reasoning": "llama3.2",
        
        # Quick responses
        "fast": "phi3:mini",
        
        # Instruction following
        "instructions": "mistral-nemo",
        
        # Creative tasks
        "creative": "gemma2:9b",
        
        # Vision understanding
        "vision": "llava",
        
        # Code generation - use mistral instead of qwen
        "code": "mistral-nemo"
    }
    
    def select_model(self, text: str) -> str:
        """Select best model based on user input."""
        text_lower = text.lower()
        
        # Code-related queries
        if any(word in text_lower for word in ["code", "python", "javascript", "program", "function", "debug"]):
            return self.MODELS["code"]
        
        # Reasoning tasks
        if any(word in text_lower for word in ["explain", "why", "how does", "reason", "think about"]):
            return self.MODELS["reasoning"]
        
        # Vision tasks
        if any(word in text_lower for word in ["look at", "see", "image", "picture", "photo"]):
            return self.MODELS["vision"]
        
        # Creative tasks
        if any(word in text_lower for word in ["story", "poem", "creative", "imagine", "write"]):
            return self.MODELS["creative"]
        
        # Quick questions
        if any(word in text_lower for word in ["what time", "what date", "weather", "quick"]):
            return self.MODELS["fast"]
        
        # Default to best general model
        return self.MODELS["general"]
    
    def get_model_info(self, model_type: str) -> dict:
        """Get information about a model type."""
        model = self.MODELS.get(model_type, self.MODELS["general"])
        return {
            "name": model,
            "type": model_type,
            "description": self.get_description(model_type)
        }
    
    def get_description(self, model_type: str) -> str:
        """Get description of model capabilities."""
        descriptions = {
            "general": "Balanced model for general conversation",
            "reasoning": "Advanced reasoning and problem-solving",
            "fast": "Quick responses for simple queries",
            "instructions": "Excellent at following complex instructions",
            "creative": "Creative writing and imagination",
            "vision": "Can understand and describe images",
            "code": "Programming and code generation"
        }
        return descriptions.get(model_type, "General purpose AI")
