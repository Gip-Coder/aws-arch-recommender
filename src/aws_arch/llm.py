"""Thin Bedrock wrapper with an on-disk cache so repeated dev runs cost nothing."""
import hashlib
import json
import os
from pathlib import Path
from .common import ROOT

CACHE = ROOT / ".cache"

_TOKEN_USAGE = {
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "calls": 0,
}

def load_env_file(env_path: Path | None = None) -> None:
    """Load key-value pairs from .env if present into os.environ without overriding existing ones."""
    if env_path is None:
        env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

def get_bedrock_config(model_id: str | None = None, region: str | None = None) -> tuple[str, str]:
    """Retrieve and validate Bedrock model_id and region."""
    load_env_file()
    resolved_model = model_id or os.environ.get("BEDROCK_MODEL_ID", "").strip()
    if not resolved_model:
        raise ValueError(
            "BEDROCK_MODEL_ID is not configured. "
            "Please set BEDROCK_MODEL_ID in your environment or in .env, "
            "or provide it using the --model flag. "
            "Example: BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0"
        )
    resolved_region = region or os.environ.get("AWS_REGION", "ap-south-1").strip()
    return resolved_model, resolved_region

def get_token_usage() -> dict:
    """Return accumulated token usage across LLM calls."""
    return dict(_TOKEN_USAGE)

def reset_token_usage() -> None:
    """Reset accumulated token counters."""
    _TOKEN_USAGE["total_input_tokens"] = 0
    _TOKEN_USAGE["total_output_tokens"] = 0
    _TOKEN_USAGE["calls"] = 0

def call_llm(
    system: str,
    user: str,
    model_id: str | None = None,
    region: str | None = None,
    use_cache: bool = True,
) -> str:
    resolved_model, resolved_region = get_bedrock_config(model_id, region)

    if os.environ.get("AWS_ARCH_NO_CACHE") == "1":
        use_cache = False

    if use_cache:
        CACHE.mkdir(exist_ok=True)
        key = hashlib.sha256(f"{resolved_model}|{system}|{user}".encode("utf-8")).hexdigest()
        f = CACHE / f"{key}.txt"
        if f.exists():
            return f.read_text(encoding="utf-8")

    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

    try:
        client = boto3.client("bedrock-runtime", region_name=resolved_region)
        resp = client.converse(
            modelId=resolved_model,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"temperature": 0.1, "maxTokens": 1500},
        )
    except (NoCredentialsError, PartialCredentialsError) as e:
        raise RuntimeError(
            "AWS credentials not found or incomplete. Run 'aws configure' or set AWS_ACCESS_KEY_ID "
            "and AWS_SECRET_ACCESS_KEY in your environment."
        ) from e
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise RuntimeError(
                f"Access Denied for Bedrock model '{resolved_model}' in region '{resolved_region}'. "
                "Ensure your IAM user/role has 'bedrock:InvokeModel' permission and that model access "
                "is enabled in the AWS Bedrock Console for this region."
            ) from e
        elif code == "ResourceNotFoundException":
            raise RuntimeError(
                f"Bedrock model '{resolved_model}' was not found in region '{resolved_region}'. "
                "Verify the model ID and check whether this model is supported in your region."
            ) from e
        elif code in ("ThrottlingException", "TooManyRequestsException"):
            raise RuntimeError(
                f"Bedrock request throttled for model '{resolved_model}'. "
                "Retry after a short delay or request a quota increase."
            ) from e
        elif code in ("ModelTimeoutException", "RequestTimeoutException"):
            raise RuntimeError(
                f"Bedrock request timed out for model '{resolved_model}'. Please retry."
            ) from e
        else:
            raise RuntimeError(f"Bedrock invocation failed [{code}]: {msg}") from e

    usage = resp.get("usage", {})
    in_tokens = usage.get("inputTokens", 0)
    out_tokens = usage.get("outputTokens", 0)
    _TOKEN_USAGE["total_input_tokens"] += in_tokens
    _TOKEN_USAGE["total_output_tokens"] += out_tokens
    _TOKEN_USAGE["calls"] += 1

    text = resp["output"]["message"]["content"][0]["text"]
    if use_cache:
        f.write_text(text, encoding="utf-8")
    return text

def parse_json_reply(text: str) -> dict:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)
