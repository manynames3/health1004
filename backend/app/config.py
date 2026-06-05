from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore", populate_by_name=True)

    aws_region: str = Field(default="", alias="AWS_REGION")
    s3_bucket: str = Field(default="", alias="S3_BUCKET")
    opensearch_endpoint: str = Field(default="", alias="OPENSEARCH_ENDPOINT")
    opensearch_index: str = Field(default="korean-health-chunks", alias="OPENSEARCH_INDEX")
    opensearch_service: str = Field(default="aoss", alias="OPENSEARCH_SERVICE")
    opensearch_vector_dimension: int = Field(default=1024, alias="OPENSEARCH_VECTOR_DIMENSION")

    bedrock_embed_model_id: str = Field(
        default="cohere.embed-multilingual-v3", alias="BEDROCK_EMBED_MODEL_ID"
    )
    bedrock_chat_model_id: str = Field(default="", alias="BEDROCK_CHAT_MODEL_ID")
    bedrock_max_tokens: int = Field(default=1200, alias="BEDROCK_MAX_TOKENS")
    bedrock_temperature: float = Field(default=0.1, alias="BEDROCK_TEMPERATURE")

    frontend_base_url: str = Field(default="http://localhost:3000", alias="FRONTEND_BASE_URL")
    cors_allow_origins: str = Field(
        default="http://localhost:3000", alias="CORS_ALLOW_ORIGINS"
    )

    extracted_prefix: str = Field(default="extracted/", alias="EXTRACTED_PREFIX")
    reports_prefix: str = Field(default="ingestion-reports/", alias="REPORTS_PREFIX")
    metadata_key: str = Field(default="metadata/documents.json", alias="METADATA_KEY")
    presigned_url_ttl_seconds: int = Field(default=3600, alias="PRESIGNED_URL_TTL_SECONDS")

    request_body_limit_bytes: int = Field(default=16_384, alias="REQUEST_BODY_LIMIT_BYTES")
    rate_limit_per_minute: int = Field(default=30, alias="RATE_LIMIT_PER_MINUTE")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    def require_aws_runtime(self) -> None:
        missing = [
            name
            for name, value in {
                "AWS_REGION": self.aws_region,
                "S3_BUCKET": self.s3_bucket,
                "OPENSEARCH_ENDPOINT": self.opensearch_endpoint,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required AWS runtime setting(s): {', '.join(missing)}")

    def require_chat_model(self) -> None:
        if not self.bedrock_chat_model_id:
            raise RuntimeError("Missing required setting: BEDROCK_CHAT_MODEL_ID")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings(_env_file: Optional[str] = None) -> Settings:
    if _env_file:
        return Settings(_env_file=_env_file)
    return Settings()
