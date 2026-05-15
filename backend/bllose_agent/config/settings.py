from pydantic_settings import BaseSettings
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAIEmbeddings


class Settings(BaseSettings):
    # ---- 基础 LLM ----
    anthropic_api_key: str = "sk-ant-your-key-here"
    anthropic_base_url: str = ""
    llm_model: str = "claude-sonnet-4-6"

    # ---- 小模型（未配置则退回基础 LLM） ----
    small_llm_model: str = ""
    small_llm_api_key: str = ""
    small_llm_base_url: str = ""

    # ---- 推理模型（未配置则退回基础 LLM） ----
    logic_llm_model: str = ""
    logic_llm_api_key: str = ""
    logic_llm_base_url: str = ""

    # ---- 嵌入模型 ----
    embedding_llm_model: str = "text-embedding-3-small"
    embedding_llm_api_key: str = ""
    embedding_llm_base_url: str = ""

    # ---- Server ----
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # ── helpers ──────────────────────────────────────────────

    def _resolve(self, model: str, api_key: str, base_url: str) -> tuple[str, str, str]:
        """未配置的值退回基础 LLM 对应字段"""
        return (
            model or self.llm_model,
            api_key or self.anthropic_api_key,
            base_url or self.anthropic_base_url,
        )

    # ── get 方法 ─────────────────────────────────────────────

    def _build_chat_anthropic(self, model: str, api_key: str, base_url: str, **kwargs) -> ChatAnthropic:
        extra: dict[str, str] = {}
        if base_url:
            extra["base_url"] = base_url
        return ChatAnthropic(model=model, api_key=api_key, **extra, **kwargs)

    def get_llm(self, **kwargs) -> ChatAnthropic:
        return self._build_chat_anthropic(
            self.llm_model, self.anthropic_api_key, self.anthropic_base_url, **kwargs
        )

    def get_small_llm(self, **kwargs) -> ChatAnthropic:
        model, api_key, base_url = self._resolve(
            self.small_llm_model, self.small_llm_api_key, self.small_llm_base_url,
        )
        return self._build_chat_anthropic(model, api_key, base_url, **kwargs)

    def get_logic_llm(self, **kwargs) -> ChatAnthropic:
        model, api_key, base_url = self._resolve(
            self.logic_llm_model, self.logic_llm_api_key, self.logic_llm_base_url,
        )
        return self._build_chat_anthropic(model, api_key, base_url, **kwargs)

    def get_embedding_llm(self, **kwargs) -> OpenAIEmbeddings:
        extra: dict[str, str] = {}
        if self.embedding_llm_base_url:
            extra["base_url"] = self.embedding_llm_base_url
        return OpenAIEmbeddings(
            model=self.embedding_llm_model,
            api_key=self.embedding_llm_api_key or self.anthropic_api_key,
            **extra,
            **kwargs,
        )


settings = Settings()
