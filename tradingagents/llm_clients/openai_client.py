import os
import warnings
from typing import Any, Optional

from langchain_openai import ChatOpenAI

from .base_client import BaseLLMClient
from .validators import validate_model


class UnifiedChatOpenAI(ChatOpenAI):
    """ChatOpenAI subclass that strips temperature/top_p for GPT-5 family models.

    GPT-5 family models use reasoning natively. temperature/top_p are only
    accepted when reasoning.effort is 'none'; with any other effort level
    (or for older GPT-5/GPT-5-mini/GPT-5-nano which always reason) the API
    rejects these params. Langchain defaults temperature=0.7, so we must
    strip it to avoid errors.

    Non-GPT-5 models (GPT-4.1, xAI, Ollama, etc.) are unaffected.
    """

    def __init__(self, **kwargs):
        if "gpt-5" in kwargs.get("model", "").lower():
            kwargs.pop("temperature", None)
            kwargs.pop("top_p", None)
        super().__init__(**kwargs)


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI, Ollama, OpenRouter, xAI, DeepSeek, and DashScope providers."""

    # Provider-specific base URLs and env var names
    _PROVIDER_CONFIG = {
        "xai": ("https://api.x.ai/v1", "XAI_API_KEY"),
        "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
        "ollama": ("http://localhost:11434/v1", None),
        "deepseek": ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
        "dashscope": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY"),
    }

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "openai",
        **kwargs,
    ):
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def get_llm(self) -> Any:
        """Return configured ChatOpenAI instance."""
        if not self.validate_model():
            warnings.warn(
                f"Model '{self.model}' is not in the known model list for provider "
                f"'{self.provider}'. It may still work if the provider supports it.",
                stacklevel=2,
            )

        llm_kwargs = {"model": self.model}

        if self.provider in self._PROVIDER_CONFIG:
            default_url, env_key = self._PROVIDER_CONFIG[self.provider]
            llm_kwargs["base_url"] = default_url
            if self.provider == "ollama":
                llm_kwargs["api_key"] = "ollama"
            elif env_key:
                api_key = os.environ.get(env_key)
                if api_key:
                    llm_kwargs["api_key"] = api_key
        elif self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in ("timeout", "max_retries", "reasoning_effort", "api_key", "callbacks", "http_client", "http_async_client"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        return UnifiedChatOpenAI(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for the provider."""
        return validate_model(self.provider, self.model)
