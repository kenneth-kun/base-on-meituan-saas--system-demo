from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Meituan Merchant SaaS"
    # 骨架阶段默认 SQLite，生产切 PostgreSQL（改 .env 即可）
    database_url: str = "sqlite:///./meituan_saas.db"
    # [LEGACY] 骨架阶段无版本前缀
    # api_prefix: str = "/api"
    api_prefix: str = "/api/v1"  # 版本化前缀，前端 baseURL 与 vite proxy 已同步
    # DeepSeek（LLM 底座）
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    # Embedding（RAG 底座）：默认 local 离线向量，生产可切 openai 兼容接口
    embedding_provider: str = "local"  # local | openai
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1024  # local 用 1024；openai 用 1536
    # JWT 鉴权
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_expire_days: int = 7
    # 定时刷新数据（分钟）
    refresh_interval_minutes: int = 5
    # 微信小程序（登录用，注册小程序后填写）
    wx_appid: str = ""
    wx_secret: str = ""


settings = Settings()
