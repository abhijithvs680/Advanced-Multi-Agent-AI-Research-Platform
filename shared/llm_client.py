"""
LLM Client - Unified interface for language model interactions.
Supports OpenAI GPT and Anthropic Claude with structured outputs.
"""
import os
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio

from tenacity import retry, stop_after_attempt, wait_exponential
from shared.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMResponse:
    """Structured response from LLM"""
    content: str
    model: str
    provider: LLMProvider
    usage: Dict[str, int]
    raw_response: Any = None
    
    def as_json(self) -> Optional[Dict]:
        """Parse content as JSON if possible"""
        try:
            return json.loads(self.content)
        except json.JSONDecodeError:
            return None


class LLMClient:
    """
    Unified LLM client supporting multiple providers.
    
    Features:
    - Automatic retries with exponential backoff
    - Structured output parsing
    - Token usage tracking
    - Rate limiting
    """
    
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        self.provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Set default models
        if model:
            self.model = model
        else:
            self.model = "gpt-4-turbo-preview" if provider == LLMProvider.OPENAI else "claude-3-sonnet-20240229"
        
        # Initialize client based on provider
        if provider == LLMProvider.OPENAI:
            self._init_openai(api_key)
        else:
            self._init_anthropic(api_key)
        
        logger.info("llm_client_initialized", provider=provider.value, model=self.model)
    
    def _init_openai(self, api_key: Optional[str]):
        """Initialize OpenAI client"""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY")
            )
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def _init_anthropic(self, api_key: Optional[str]):
        """Initialize Anthropic client"""
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
            )
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_output: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            json_output: Whether to request JSON output
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with content and metadata
        """
        if self.provider == LLMProvider.OPENAI:
            return await self._openai_complete(prompt, system_prompt, json_output, **kwargs)
        else:
            return await self._anthropic_complete(prompt, system_prompt, json_output, **kwargs)
    
    async def _openai_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_output: bool,
        **kwargs
    ) -> LLMResponse:
        """OpenAI completion"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response_format = {"type": "json_object"} if json_output else None
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            response_format=response_format,
            **kwargs
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider=self.provider,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            raw_response=response
        )
    
    async def _anthropic_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_output: bool,
        **kwargs
    ) -> LLMResponse:
        """Anthropic completion"""
        if json_output and system_prompt:
            system_prompt += "\n\nRespond with valid JSON only."
        elif json_output:
            system_prompt = "Respond with valid JSON only."
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            provider=self.provider,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            raw_response=response
        )
    
    async def structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured output matching a schema.
        
        Args:
            prompt: User prompt
            output_schema: JSON schema for expected output
            system_prompt: Optional additional system context
            
        Returns:
            Parsed JSON matching schema
        """
        schema_instruction = f"""
You must respond with a valid JSON object that matches this schema:
{json.dumps(output_schema, indent=2)}

Only output the JSON, no other text.
"""
        
        full_system = f"{system_prompt}\n\n{schema_instruction}" if system_prompt else schema_instruction
        
        response = await self.complete(
            prompt=prompt,
            system_prompt=full_system,
            json_output=True
        )
        
        result = response.as_json()
        if result is None:
            raise ValueError(f"Failed to parse LLM response as JSON: {response.content[:200]}")
        
        return result


# Convenience factory functions
def get_openai_client(model: str = "gpt-4-turbo-preview", **kwargs) -> LLMClient:
    """Get an OpenAI client"""
    return LLMClient(provider=LLMProvider.OPENAI, model=model, **kwargs)


def get_anthropic_client(model: str = "claude-3-sonnet-20240229", **kwargs) -> LLMClient:
    """Get an Anthropic client"""
    return LLMClient(provider=LLMProvider.ANTHROPIC, model=model, **kwargs)


def get_default_client(**kwargs) -> LLMClient:
    """Get the default LLM client based on available API keys"""
    if os.getenv("OPENAI_API_KEY"):
        return get_openai_client(**kwargs)
    elif os.getenv("ANTHROPIC_API_KEY"):
        return get_anthropic_client(**kwargs)
    else:
        raise ValueError("No LLM API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
