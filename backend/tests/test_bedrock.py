import json

from app.bedrock import BedrockRuntime
from app.config import Settings


class FakeBody:
    def __init__(self, payload: dict):
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class FakeBedrockClient:
    def __init__(self):
        self.invoke_calls = []
        self.converse_calls = []

    def invoke_model(self, **kwargs):
        self.invoke_calls.append(kwargs)
        body = json.loads(kwargs["body"].decode("utf-8"))
        return {"body": FakeBody({"embedding": [0.1] * body["dimensions"]})}

    def converse(self, **kwargs):
        self.converse_calls.append(kwargs)
        if len(self.converse_calls) == 1:
            raise RuntimeError("primary unavailable")
        return {"output": {"message": {"content": [{"text": "fallback answer"}]}}}


def runtime_with_fake_client(settings: Settings, client: FakeBedrockClient) -> BedrockRuntime:
    runtime = BedrockRuntime.__new__(BedrockRuntime)
    runtime.settings = settings
    runtime.client = client
    return runtime


def test_titan_embedding_uses_titan_request_shape():
    client = FakeBedrockClient()
    settings = Settings(
        AWS_REGION="us-east-1",
        BEDROCK_EMBED_MODEL_ID="amazon.titan-embed-text-v2:0",
        VECTOR_DIMENSION=3,
    )
    runtime = runtime_with_fake_client(settings, client)

    embeddings = runtime.embed_texts([" 소화 불량 자료 "], input_type="search_query")

    assert embeddings == [[0.1, 0.1, 0.1]]
    body = json.loads(client.invoke_calls[0]["body"].decode("utf-8"))
    assert client.invoke_calls[0]["modelId"] == "amazon.titan-embed-text-v2:0"
    assert body == {
        "inputText": "소화 불량 자료",
        "dimensions": 3,
        "normalize": True,
    }


def test_generate_answer_falls_back_to_secondary_model():
    client = FakeBedrockClient()
    settings = Settings(
        AWS_REGION="us-east-1",
        BEDROCK_CHAT_MODEL_ID="anthropic.claude-haiku-4-5-20251001-v1:0",
        BEDROCK_FALLBACK_CHAT_MODEL_ID="amazon.nova-2-lite-v1:0",
    )
    runtime = runtime_with_fake_client(settings, client)

    answer = runtime.generate_answer(question="질문", chunks=[], language="ko")

    assert answer == "fallback answer"
    assert [call["modelId"] for call in client.converse_calls] == [
        "anthropic.claude-haiku-4-5-20251001-v1:0",
        "amazon.nova-2-lite-v1:0",
    ]
