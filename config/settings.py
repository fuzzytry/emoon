"""Runtime configuration loaded from environment variables."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv(os.path.join("config",".env")); load_dotenv()
def _bool(name,default): return os.getenv(name,str(default)).strip().lower() in {"1","true","yes","on"}
@dataclass(frozen=True)
class Settings:
    camera_device:int=int(os.getenv("EMU_CAMERA_DEVICE","0")); mic_device:str=os.getenv("EMU_MIC_DEVICE",""); stt_model:str=os.getenv("EMU_STT_MODEL","small.en")
    llm_provider:str=os.getenv("EMU_LLM_PROVIDER","ollama/llama3.2"); llm_api_base:str=os.getenv("EMU_LLM_API_BASE","http://localhost:11434"); llm_api_key:str=os.getenv("EMU_LLM_API_KEY",""); use_mock_llm:bool=_bool("EMU_USE_MOCK_LLM",False)
    serial_port:str=os.getenv("EMU_SERIAL_PORT",""); serial_baud:int=int(os.getenv("EMU_SERIAL_BAUD","9600")); privacy_default:bool=_bool("EMU_PRIVACY_DEFAULT",False)
settings=Settings()
