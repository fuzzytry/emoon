"""
Provider-agnostic LLM client via LiteLLM. Never locks to one vendor —
settings.llm_provider selects OpenAI/Anthropic/Gemini/Ollama/etc. by name.
A mock mode is included so the system is runnable with zero API keys and
zero internet — this is what --simulate uses by default.
"""
import json
import logging
from config.settings import settings

logger = logging.getLogger("emu.llm")


class MockLLM:
    """Deterministic, zero-dependency stand-in for local testing. Produces
    plausible structured output without any network call — this is what
    makes `python main.py --simulate` runnable on a machine with no API
    keys and no Ollama installed."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        text_lower = user_prompt.lower()
        if "sad" in text_lower or "terrible" in text_lower or "tired" in text_lower:
            return json.dumps({
                "intent": "SUPPORT", "emotion": "SAD",
                "speech": "That sounds rough. Want to tell me what happened?",
                "gesture": "GENTLE_ATTENTION", "expression": "CONCERNED",
                "lighting": "CALM",
            })
        if "back" in text_lower or "hey" in text_lower:
            return json.dumps({
                "intent": "GREET", "emotion": "HAPPY",
                "speech": "Welcome back.",
                "gesture": "WAVE", "expression": "HAPPY",
                "lighting": "HAPPY",
            })
        return json.dumps({
            "intent": "IDLE_CHAT", "emotion": "NEUTRAL",
            "speech": "I'm here if you need anything.",
            "gesture": "NONE", "expression": "NEUTRAL",
            "lighting": "IDLE",
        })


class LLMClient:
    def __init__(self):
        self._mock = settings.use_mock_llm
        if not self._mock:
            import litellm  # imported lazily so mock mode has zero extra deps
            self._litellm = litellm
        else:
            self._mock_client = MockLLM()

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if self._mock:
            return self._mock_client.complete(system_prompt, user_prompt)
        try:
            response = self._litellm.completion(
                model=settings.llm_provider,
                api_key=settings.llm_api_key or None,
                api_base=settings.llm_api_base or None,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=15,
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("LLM call failed (%s) — falling back to mock response", e)
            return MockLLM().complete(system_prompt, user_prompt)
