from __future__ import annotations
import re

class RouterModule:
    COMPLEX_MARKERS = [
        "напиши", "разработай", "проанализируй", "исправь", "реализуй", "спроектируй",
        "write", "develop", "analyze", "fix", "implement", "design"
    ]

    @staticmethod
    def classify(text: str) -> str:
        # Check word count
        words = text.split()
        if len(words) >= 30:
            return "complex"
        
        # Check task markers
        text_lower = text.lower()
        for marker in RouterModule.COMPLEX_MARKERS:
            if marker in text_lower:
                return "complex"
        
        # Check for code blocks
        if "```" in text:
            return "complex"
            
        return "simple"

    @staticmethod
    def select_model(prompt: str, cfg) -> tuple[str, str, str | None]:
        """
        Returns (provider_name, model_name, api_key)
        
        Logic per §40.1 + §42.2:
        - simple: qwen/qwen3-coder:free (OpenRouter) or gemini-1.5-flash
        - complex: deepseek/deepseek-r1 (OpenRouter) or nvidia/llama-3.1-nemotron-70b-instruct
        """
        complexity = RouterModule.classify(prompt)
        
        # Priority 1: NVIDIA if key exists
        nv_key = cfg.nvidia_key
        if nv_key:
            if complexity == "complex":
                return "NVIDIA", "nvidia/llama-3.1-nemotron-70b-instruct", nv_key
            else:
                # Use a smaller model if available or just stick to a good default
                return "NVIDIA", "nvidia/llama-3.1-nemotron-70b-instruct", nv_key

        # Priority 2: OpenRouter
        or_key = cfg.default_openrouter_key()
        if or_key:
            key_val = or_key["key"]
            if complexity == "complex":
                return "OpenRouter", "deepseek/deepseek-r1", key_val
            else:
                return "OpenRouter", "qwen/qwen3-coder:free", key_val

        # Priority 3: FavoriteAPI
        fav_key = cfg.default_favorite_key()
        if fav_key:
            return "FavoriteAPI", fav_key.get("model", "gemini-3.0-flash-thinking"), fav_key["key"]

        raise RuntimeError("No LLM providers configured")
