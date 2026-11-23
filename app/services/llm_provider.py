"""
LLM provider layer (Strategy pattern).

rag.py and synthesis.py only depend on the LLMProvider interface.
Which concrete provider is used is decided by config (LLM_PROVIDER in .env),
so switching between local Ollama and cloud Groq needs no code changes.
"""
from abc import ABC, abstractmethod

from app.config import settings


class LLMProvider(ABC):
    """Common interface every LLM backend must implement."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...


class OllamaProvider(LLMProvider):
    def __init__(self, temperature: float = 0.1):
        from langchain_ollama import OllamaLLM

        self._llm = OllamaLLM(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )

    def generate(self, prompt: str) -> str:
        return self._llm.invoke(prompt).strip()


class GroqProvider(LLMProvider):
    def __init__(self, temperature: float = 0.1):
        from langchain_groq import ChatGroq

        if not settings.groq_api_key:
            raise ValueError("LLM_PROVIDER=groq but GROQ_API_KEY is not set in .env")

        self._llm = ChatGroq(
            model=settings.groq_llm_model,
            api_key=settings.groq_api_key,
            temperature=temperature,
        )

    def generate(self, prompt: str) -> str:
        # ChatGroq returns a message object; the text is in .content
        return self._llm.invoke(prompt).content.strip()


_PROVIDERS = {
    "ollama": OllamaProvider,
    "groq": GroqProvider,
}


def get_llm_provider(temperature: float = 0.1) -> LLMProvider:
    """Factory: build the provider named in config."""
    name = settings.llm_provider.lower()
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown LLM_PROVIDER '{name}'. Use one of: {', '.join(_PROVIDERS)}")
    print(f"[Klaris] LLM provider: {name}, model: {settings.groq_llm_model if name == 'groq' else settings.ollama_llm_model}")
    return _PROVIDERS[name](temperature=temperature)