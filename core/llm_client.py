from typing import Optional, Dict, Any
from langchain_core.language_models import BaseLanguageModel
from langchain_ollama import OllamaLLM
from settings import settings


class LLMClient:
    """
    LLM client that uses LangChain's built-in model abstraction.
    Can be configured via settings or configuration files.
    
    Example:
        # From settings
        client = LLMClient.from_settings()
        
        # With custom config
        client = LLMClient(
            provider="ollama",
            model_name="gemma3:4b",
            temperature=0.5
        )
        
        # Use the LangChain LLM directly
        response = client.llm.invoke("What is a book?")
    """
    
    def __init__(
        self,
        provider: str = "ollama",
        model_name: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize LLM client.
        
        Args:
            provider: Provider type ("ollama", "openai", "anthropic", etc.)
            model_name: Model name (if None, uses default from settings)
            **kwargs: Provider-specific parameters
        """
        self.provider = provider
        self.model_name = model_name or getattr(settings, "default_llm_model", "gemma3:1b")
        self.config = kwargs
        self._llm: Optional[BaseLanguageModel] = None
    
    @classmethod
    def from_settings(cls) -> "LLMClient":
        """
        Create LLM client from application settings.
        
        Returns:
            Configured LLMClient instance
        """
        provider = getattr(settings, "default_llm_provider", "ollama")
        model_name = getattr(settings, "default_llm_model", "gemma3:1b")
        
        # Build config from settings
        config: Dict[str, Any] = {}
        
        if provider == "ollama":
            # base_url is optional - OllamaLLM defaults to http://localhost:11434
            # Only set it if it's explicitly configured
            if hasattr(settings, "ollama_base_url"):
                config["base_url"] = settings.ollama_base_url
            config["temperature"] = getattr(settings, "llm_temperature", 0.7)
        
        return cls(provider=provider, model_name=model_name, **config)
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "LLMClient":
        """
        Create LLM client from a configuration dictionary.
        Useful for loading from JSON/YAML config files.
        
        Args:
            config: Configuration dictionary with keys:
                - provider: Provider type (required)
                - model_name: Model name (required)
                - Any provider-specific parameters
        
        Returns:
            Configured LLMClient instance
            
        Example:
            config = {
                "provider": "ollama",
                "model_name": "gemma3:4b",
                "temperature": 0.5,
                "base_url": "http://localhost:11434"
            }
            client = LLMClient.from_config(config)
        """
        config = config.copy()
        provider = config.pop("provider", "ollama")
        model_name = config.pop("model_name", None)
        
        return cls(provider=provider, model_name=model_name, **config)
    
    @property
    def llm(self) -> BaseLanguageModel:
        """
        Get the LangChain LLM instance (lazy initialization).
        
        Returns:
            LangChain LLM instance implementing BaseLanguageModel
        """
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    def _create_llm(self) -> BaseLanguageModel:
        """
        Create the LangChain LLM instance based on provider.
        
        Returns:
            LangChain LLM instance
        """
        if self.provider == "ollama":
            base_url = self.config.get("base_url", "http://localhost:11434")
            temperature = self.config.get("temperature", 0.7)
            
            return OllamaLLM(
                model=self.model_name,
                base_url=base_url,
                temperature=temperature,
                **{k: v for k, v in self.config.items() if k not in ["base_url", "temperature"]}
            )
        
        elif self.provider == "openai":
            # Future: Add OpenAI support
            # from langchain_openai import ChatOpenAI
            # return ChatOpenAI(model=self.model_name, **self.config)
            raise NotImplementedError(f"Provider '{self.provider}' not yet implemented")
        
        elif self.provider == "anthropic":
            # Future: Add Anthropic support
            # from langchain_anthropic import ChatAnthropic
            # return ChatAnthropic(model=self.model_name, **self.config)
            raise NotImplementedError(f"Provider '{self.provider}' not yet implemented")
        
        else:
            available = ["ollama"]  # Add more as you implement them
            raise ValueError(
                f"Unsupported provider: '{self.provider}'. "
                f"Available providers: {', '.join(available)}"
            )
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the current LLM configuration.
        
        Returns:
            Dictionary with LLM information
        """
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "config": self.config,
        }
    
    def update_config(self, **kwargs) -> None:
        """
        Update configuration and reset LLM instance.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        self.config.update(kwargs)
        self._llm = None  # Reset to force recreation with new config
    
    def reset(self) -> None:
        """Reset the LLM instance (force recreation on next access)."""
        self._llm = None
