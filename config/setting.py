"""
Central configuration for EMU. Loads from environment variables — never
hard-code secrets or providers here. See .env.example for all keys.
"""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional; env vars can be set directly instead


@dataclass
class Settings:
    log_level: str = os.getenv("EMU_LOG_LEVEL", "INFO")

    # Perception — not wired yet (Phase 2)
    camera_device: int = int(os.getenv("EMU_CAMERA_DEVICE", "0"))
    mic_device: str = os.getenv("EMU_MIC_DEVICE", "default")
    stt_model: str = os.getenv("EMU_STT_MODEL", "small.en")

    # Intelligence — provider-agnostic via LiteLLM naming convention,
    # e.g. "ollama/llama3", "anthropic/claude-3-5-haiku", "openai/gpt-4o-mini"
    llm_provider: str = os.getenv("EMU_LLM_PROVIDER", "ollama/llama3")
    llm_api_key: str = os.getenv("EMU_LLM_API_KEY", "")
    llm_api_base: str = os.getenv("EMU_LLM_API_BASE", "")
    use_mock_llm: bool = os.getenv("EMU_USE_MOCK_LLM", "true").lower() == "true"

    # Hardware — empty port means "no physical robot", commands are logged only
    serial_port: str = os.getenv("EMU_SERIAL_PORT", "")
    serial_baud: int = int(os.getenv("EMU_SERIAL_BAUD", "9600"))

    # Privacy
    privacy_default: bool = os.getenv("EMU_PRIVACY_DEFAULT", "false").lower() == "true"


settings = Settings()
