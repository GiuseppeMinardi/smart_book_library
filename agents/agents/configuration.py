from typing import Any, Literal, Optional

from fastmcp import settings
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelSettings(BaseSettings):
    # Automatically read matching environment variables (and optional .env file)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    provider: Literal["openai", "gemini", "ollama", "anthropic"] = Field(
        ..., description="The LLM provider to use for tasks"
    )
    model_name: str = Field(
        ..., description="The specific model name to use for LLM tasks"
    )
    # Using 'str' is safer here than 'HttpUrl' as the underlying vendor SDKs 
    # (like httpx or OpenAI's client) expect string types for base URLs.
    base_url: Optional[str] = Field(
        None, description="The base URL for the LLM API"
    )
    api_key: Optional[SecretStr] = Field(
        None, description="API key for authenticating with the LLM provider"
    )

    @model_validator(mode="after")
    def validate_api_key(self) -> "ModelSettings":
        """Ensure an API key is provided for hosted models."""
        if self.provider in {"openai", "gemini", "anthropic"} and not self.api_key:
            raise ValueError(f"API key is required for provider '{self.provider}'")
        return self

    @model_validator(mode="after")
    def validate_base_url(self) -> "ModelSettings":
        """Ensure a Base URL is provided for self-hosted Ollama."""
        if self.provider == "ollama" and not self.base_url:
            raise ValueError(f"Base URL is required for provider '{self.provider}'")
        return self

    def get_pydantic_ai_model(self) -> Any:
        """
        Dynamically initializes and returns the correct Pydantic AI model 
        and provider based on the validated environment variables.
        """
        # Unmask the SecretStr to a raw string for the SDKs
        key_str = self.api_key.get_secret_value() if self.api_key else None
        print(
            f"Initializing model with provider '{self.provider}' and model name '{self.model_name}'"
        )

        if self.provider == "openai":
            print("Using OpenAI provider with model:", self.model_name)
            from pydantic_ai.models.openai import OpenAIChatModel
            from pydantic_ai.providers.openai import OpenAIProvider

            provider_kwargs = {"api_key": key_str}
                
            return OpenAIChatModel(
                self.model_name, 
                provider=OpenAIProvider(**provider_kwargs),
            )

        elif self.provider == "anthropic":
            print("Using Anthropic provider with model:", self.model_name)
            from pydantic_ai.models.anthropic import AnthropicModel
            from pydantic_ai.providers.anthropic import AnthropicProvider

            provider_kwargs = {"api_key": key_str}
                
            return AnthropicModel(
                self.model_name, 
                provider=AnthropicProvider(**provider_kwargs)
            )

        elif self.provider == "gemini":
            from pydantic_ai.models.google import GoogleModel
            from pydantic_ai.providers.google import GoogleProvider
            
            return GoogleModel(
                self.model_name, 
                provider=GoogleProvider(api_key=key_str)
            )

        elif self.provider == "ollama":
            from pydantic_ai.models.ollama import OllamaModel
            from pydantic_ai.providers.ollama import OllamaProvider
            
            return OllamaModel(
                self.model_name, provider=OllamaProvider(base_url=self.base_url + "/v1")
            )


settings = ModelSettings()