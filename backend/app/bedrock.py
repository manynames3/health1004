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
        model_id = self.settings.bedrock_embed_model_id
        if _is_titan_embed_model(model_id):
            return [self._embed_titan_text(text) for text in texts]

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

    def _embed_titan_text(self, text: str) -> list[float]:
        body = {
            "inputText": _clip_for_titan(text),
            "dimensions": self.settings.vector_dimension,
            "normalize": True,
        }
        response = self.client.invoke_model(
            modelId=self.settings.bedrock_embed_model_id,
            body=json.dumps(body).encode("utf-8"),
            accept="application/json",
            contentType="application/json",
        )
        payload = json.loads(response["body"].read())
        embedding = payload.get("embedding")
        if embedding is None:
            raise RuntimeError(f"Unexpected Titan embedding response shape: {payload.keys()}")
        return embedding

    def generate_answer(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
        language: LanguageCode,
    ) -> str:
        self.settings.require_chat_model()
        user_prompt = build_user_prompt(question, chunks, language)
        model_ids = [
            self.settings.bedrock_chat_model_id,
            self.settings.bedrock_fallback_chat_model_id,
        ]
        unique_model_ids = [
            model_id
            for index, model_id in enumerate(model_ids)
            if model_id and model_id not in model_ids[:index]
        ]
        last_error: Exception | None = None
        for model_id in unique_model_ids:
            try:
                return self._generate_answer_with_model(model_id, user_prompt)
            except Exception as exc:
                last_error = exc
                logger.exception("Bedrock Converse call failed for model %s", model_id)
        if last_error:
            raise last_error
        raise RuntimeError("No Bedrock answer model is configured")

    def _generate_answer_with_model(self, model_id: str, user_prompt: str) -> str:
        response = self.client.converse(
            modelId=model_id,
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


def _clip_for_cohere(text: str) -> str:
    # Cohere Embed v3 on Bedrock limits each text to roughly 2,048 characters.
    compact = " ".join((text or "").split())
    return compact[:2048]


def _clip_for_titan(text: str) -> str:
    # Titan Text Embeddings V2 accepts up to 50,000 characters.
    compact = " ".join((text or "").split())
    return compact[:50000]


def _is_titan_embed_model(model_id: str) -> bool:
    return model_id.startswith("amazon.titan-embed-text")
