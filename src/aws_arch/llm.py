"""Thin Bedrock wrapper with an on-disk cache so repeated dev runs cost nothing."""
import hashlib, json
from .common import ROOT

CACHE = ROOT / ".cache"

def call_llm(system: str, user: str, model_id: str = "REPLACE_WITH_BEDROCK_MODEL_ID",
             region: str = "ap-south-1") -> str:
    CACHE.mkdir(exist_ok=True)
    key = hashlib.sha256(f"{model_id}|{system}|{user}".encode()).hexdigest()
    f = CACHE / f"{key}.txt"
    if f.exists():
        return f.read_text()
    import boto3  # imported lazily so tests/mock mode need no AWS
    client = boto3.client("bedrock-runtime", region_name=region)
    resp = client.converse(
        modelId=model_id,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"temperature": 0.1, "maxTokens": 1500},
    )
    text = resp["output"]["message"]["content"][0]["text"]
    f.write_text(text)
    return text

def parse_json_reply(text: str) -> dict:
    text = text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)
