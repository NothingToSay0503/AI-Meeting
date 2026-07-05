from app.core.config import Settings, settings
from app.worker.asr.base import AsrProvider
from app.worker.asr.iflytek import IflytekSpeedAsrProvider
from app.worker.asr.mock import MockAsrProvider
from app.worker.llm.base import MinutesProvider
from app.worker.llm.deepseek import DeepSeekMinutesProvider
from app.worker.llm.mock import MockMinutesProvider


def build_asr_provider(settings_obj: Settings = settings) -> AsrProvider:
    if settings_obj.asr_provider == "mock":
        return MockAsrProvider()
    if settings_obj.asr_provider == "iflytek-speed":
        return IflytekSpeedAsrProvider(
            app_id=settings_obj.xfei_app_id,
            api_key=settings_obj.xfei_api_key,
            api_secret=settings_obj.xfei_api_secret,
            language=settings_obj.xfei_asr_language,
            accent=settings_obj.xfei_asr_accent,
            domain=settings_obj.xfei_asr_domain,
            vspp_on=settings_obj.xfei_asr_vspp_on,
        )
    raise ValueError(f"Unsupported ASR provider: {settings_obj.asr_provider}")


def build_minutes_provider(settings_obj: Settings = settings) -> MinutesProvider:
    if settings_obj.llm_provider == "mock":
        return MockMinutesProvider()
    if settings_obj.llm_provider == "deepseek":
        return DeepSeekMinutesProvider(
            api_key=settings_obj.llm_api_key,
            base_url=settings_obj.llm_base_url,
            model=settings_obj.llm_model,
        )
    raise ValueError(f"Unsupported LLM provider: {settings_obj.llm_provider}")
