import json
import logging
import re
import time

from config.settings import settings

logger = logging.getLogger("emu.llm")


class MockLLM:
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        t = user_prompt.lower()

        if "sad" in t or "terrible" in t:
            return json.dumps({
                "intent": "SUPPORT",
                "emotion": "SAD",
                "speech": "That sounds rough. Want to tell me what happened?",
                "gesture": "GENTLE_ATTENTION",
                "expression": "CONCERNED",
                "lighting": "CALM",
            })

        if "back" in t or "hey" in t:
            return json.dumps({
                "intent": "GREET",
                "emotion": "HAPPY",
                "speech": "Welcome back.",
                "gesture": "WAVE",
                "expression": "HAPPY",
                "lighting": "HAPPY",
            })

        return json.dumps({
            "intent": "IDLE_CHAT",
            "emotion": "NEUTRAL",
            "speech": "I'm here if you need anything.",
            "gesture": "NONE",
            "expression": "NEUTRAL",
            "lighting": "IDLE",
        })


class LLMClient:
    REQUIRED_FIELDS = {
        "intent",
        "emotion",
        "speech",
        "gesture",
        "expression",
        "lighting",
    }

    MAX_RETRIES = 2

    def __init__(self):
        self._mock = settings.use_mock_llm

        if not self._mock:
            import litellm

            self._litellm = litellm

            # Keep LiteLLM quiet unless EMU itself reports an error.
            self._litellm.suppress_debug_info = True
        else:
            self._mock_client = MockLLM()

    def _extract_json(self, content: str) -> dict:
        """
        Parse JSON returned by the model.

        Laguna normally returns clean JSON, but this also handles:
            ```json
            {...}
            ```

        and accidental text before/after the JSON object.
        """

        if not content:
            raise ValueError("LLM returned empty content")

        content = content.strip()

        # First attempt: completely clean JSON.
        try:
            parsed = json.loads(content)

            if not isinstance(parsed, dict):
                raise ValueError("LLM JSON response is not an object")

            return parsed

        except json.JSONDecodeError:
            pass

        # Remove markdown code fences.
        cleaned = re.sub(
            r"```(?:json)?\s*|\s*```",
            "",
            content,
            flags=re.IGNORECASE,
        ).strip()

        try:
            parsed = json.loads(cleaned)

            if not isinstance(parsed, dict):
                raise ValueError("LLM JSON response is not an object")

            return parsed

        except json.JSONDecodeError:
            pass

        # Last attempt: extract the first {...} object.
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end > start:
            candidate = cleaned[start:end + 1]

            try:
                parsed = json.loads(candidate)

                if not isinstance(parsed, dict):
                    raise ValueError("LLM JSON response is not an object")

                return parsed

            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Could not parse LLM JSON: {e}"
                ) from e

        raise ValueError("LLM response contained no JSON object")

    def _validate(self, parsed: dict) -> None:
        """Validate EMU's decision contract."""

        missing = self.REQUIRED_FIELDS - parsed.keys()

        if missing:
            raise ValueError(
                f"LLM response missing fields: {sorted(missing)}"
            )

        if not isinstance(parsed["speech"], str):
            raise ValueError("LLM speech field must be a string")

        if not parsed["speech"].strip():
            raise ValueError("LLM speech field is empty")

    def _fallback(self) -> str:
        """Safe response when the real LLM cannot answer."""

        return json.dumps({
            "intent": "IDLE_CHAT",
            "emotion": "CONFUSED",
            "speech": "Give me a second, I had a brain hiccup.",
            "gesture": "NONE",
            "expression": "CONFUSED",
            "lighting": "CALM",
        })

    def complete(self, system_prompt: str, user_prompt: str) -> str:

        if self._mock:
            return self._mock_client.complete(
                system_prompt,
                user_prompt,
            )

        emu_system_prompt = f"""
You are EMU, a friendly AI desktop companion.

{system_prompt}

IMPORTANT OUTPUT RULES:

- Return ONLY one valid JSON object.
- Do NOT use markdown.
- Do NOT use code fences.
- Do NOT explain your reasoning.
- Do NOT include reasoning or analysis.
- Do NOT roleplay actions such as "*whirrs*" or "*beeps*".
- The "speech" field is the ONLY text EMU will say aloud.
- Keep "speech" concise, normally under 25 words.
- Every required field must be present.
- Use ONLY the allowed values listed below.

Return exactly this structure:

{{
  "intent": "IDLE_CHAT",
  "emotion": "NEUTRAL",
  "speech": "Your response here.",
  "gesture": "NONE",
  "expression": "NEUTRAL",
  "lighting": "IDLE"
}}

Allowed expression values:
NEUTRAL, HAPPY, SAD, ANGRY, ANXIOUS, SURPRISED,
CONFUSED, CURIOUS, SLEEPY, TIRED, ALERT, CONCERNED,
LISTENING, PROCESSING, EXCITED, EMBARRASSED, PRIVACY, TALKING

Allowed gesture values:
NONE, WAVE, NOD, SHUFFLE, GENTLE_ATTENTION,
ACKNOWLEDGE

Allowed lighting values:
IDLE, HAPPY, CALM, ALERT

The JSON must contain all six fields.

Do not output anything except the JSON object.
""".strip()

        for attempt in range(self.MAX_RETRIES + 1):

            try:
                start = time.perf_counter()

                response = self._litellm.completion(
                    model=settings.llm_provider,
                    api_key=settings.llm_api_key or None,
                    api_base=settings.llm_api_base or None,
                    messages=[
                        {
                            "role": "system",
                            "content": emu_system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        },
                    ],

                    # Laguna responds much better when reasoning
                    # is explicitly excluded.
                    reasoning={
                        "exclude": True,
                    },

                    temperature=0.2,

                    # Enough room for EMU's six-field JSON.
                    max_tokens=180,

                    timeout=30,
                )

                elapsed = time.perf_counter() - start

                message = response["choices"][0]["message"]

                content = message.get("content")

                if content is None:
                    reasoning = message.get("reasoning_content")

                    if reasoning:
                        raise ValueError(
                            "LLM returned reasoning but no final content"
                        )

                    raise ValueError(
                        "LLM returned empty content"
                    )

                parsed = self._extract_json(content)

                self._validate(parsed)

                logger.info(
                    "LLM response received in %.2fs",
                    elapsed,
                )

                return json.dumps(
                    parsed,
                    ensure_ascii=False,
                )

            except Exception as e:

                logger.warning(
                    "LLM attempt %d/%d failed: %s",
                    attempt + 1,
                    self.MAX_RETRIES + 1,
                    e,
                )

                # Retry transient provider/rate-limit/network
                # failures, but don't hammer the provider.
                if attempt < self.MAX_RETRIES:
                    delay = 0.75 * (attempt + 1)
                    time.sleep(delay)
                    continue

                logger.exception("LLM call failed permanently")

        return self._fallback()