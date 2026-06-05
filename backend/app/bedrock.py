import json
import logging
from typing import Iterable

import boto3

from app.config import Settings
from app.models import LanguageCode, RetrievedChunk
from app.prompt import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class BedrockRuntime:
    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.aws_region:
            raise RuntimeError("AWS_REGION is required for Bedrock calls")
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def embed_texts(self, texts: Iterable[str], input_type: str) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        batch: list[str] = []
        for text in texts:
            batch.append(_clip_for_cohere(text))
            if len(batch) == 96:
                all_embeddings.extend(self._embed_batch(batch, input_type=input_type))
                batch = []
        if batch:
            all_embeddings.extend(self._embed_batch(batch, input_type=input_type))
        return all_embeddings

    def _embed_batch(self, texts: list[str], input_type: str) -> list[list[float]]:
        body = {
            "texts": texts,
            "input_type": input_type,
            "truncate": "END",
        }
        response = self.client.invoke_model(
            modelId=self.settings.bedrock_embed_model_id,
            body=json.dumps(body).encode("utf-8"),
            accept="application/json",
            contentType="application/json",
        )
        payload = json.loads(response["body"].read())
        embeddings = payload.get("embeddings")
        if embeddings is None:
            raise RuntimeError(f"Unexpected embedding response shape: {payload.keys()}")
        return embeddings

    def generate_answer(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
        language: LanguageCode,
    ) -> str:
        self.settings.require_chat_model()
        user_prompt = build_user_prompt(question, chunks, language)
        try:
            response = self.client.converse(
                modelId=self.settings.bedrock_chat_model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                inferenceConfig={
                    "maxTokens": self.settings.bedrock_max_tokens,
                    "temperature": self.settings.bedrock_temperature,
                },
            )
            blocks = response.get("output", {}).get("message", {}).get("content", [])
            answer = "".join(block.get("text", "") for block in blocks).strip()
            if answer:
                return answer
            raise RuntimeError("Bedrock Converse returned an empty answer")
        except Exception:
            logger.exception("Bedrock Converse call failed")
            raise


def _clip_for_cohere(text: str) -> str:
    # Cohere Embed v3 on Bedrock limits each text to roughly 2,048 characters.
    compact = " ".join((text or "").split())
    return compact[:2048]
