from typing import Any, Optional
import warnings

from langchain_anthropic import ChatAnthropic

from .base_client import BaseLLMClient
from .validators import validate_model


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic Claude models."""

    def __init__(self, model: str, base_url: Optional[str] = None, **kwargs):
        super().__init__(model, base_url, **kwargs)

    def get_llm(self) -> Any:
        """Return configured ChatAnthropic instance."""
        if not self.validate_model():
            warnings.warn(
                f"Model '{self.model}' is not in the known model list for Anthropic. "
                "It may still work if the provider supports it.",
                stacklevel=2,
            )

        llm_kwargs = {"model": self.model}

        if self.base_url:
            llm_kwargs["anthropic_api_url"] = self.base_url

        for key in ("timeout", "max_retries", "max_tokens", "callbacks", "http_client", "http_async_client"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        # Unified api_key parameter
        if "api_key" in self.kwargs:
            llm_kwargs["anthropic_api_key"] = self.kwargs["api_key"]

        return ChatAnthropic(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for Anthropic."""
        return validate_model("anthropic", self.model)
