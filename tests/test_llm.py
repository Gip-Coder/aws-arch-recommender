import os
from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from aws_arch import llm


@pytest.fixture(autouse=True)
def clean_env_and_usage(tmp_path, monkeypatch):
    llm.reset_token_usage()
    # Point cache to a temporary directory so tests don't affect repo .cache
    monkeypatch.setattr(llm, "CACHE", tmp_path / ".cache")
    # Clean up environment variables
    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_ARCH_NO_CACHE", raising=False)


def test_missing_model_id_raises_actionable_error():
    with pytest.raises(ValueError) as exc:
        llm.call_llm("sys", "user")
    assert "BEDROCK_MODEL_ID is not configured" in str(exc.value)
    assert "--model" in str(exc.value)


def test_model_id_from_flag_or_env(monkeypatch):
    monkeypatch.setenv("BEDROCK_MODEL_ID", "env-model-id")
    model, region = llm.get_bedrock_config()
    assert model == "env-model-id"
    assert region == "ap-south-1"

    # Direct override
    model_override, _ = llm.get_bedrock_config(model_id="override-model-id", region="us-east-1")
    assert model_override == "override-model-id"


def test_cache_hit_and_miss_with_mocked_boto3(monkeypatch):
    mock_boto3 = MagicMock()
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client

    mock_client.converse.return_value = {
        "output": {"message": {"content": [{"text": '{"result": "ok"}'}]}},
        "usage": {"inputTokens": 42, "outputTokens": 18},
    }

    monkeypatch.setattr("boto3.client", mock_boto3.client)
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")

    # 1. First call -> Cache miss -> Converse called
    res1 = llm.call_llm("system prompt", "user prompt")
    assert res1 == '{"result": "ok"}'
    assert mock_client.converse.call_count == 1
    usage = llm.get_token_usage()
    assert usage["total_input_tokens"] == 42
    assert usage["total_output_tokens"] == 18
    assert usage["calls"] == 1

    # 2. Second call with same arguments -> Cache hit -> Converse NOT called again
    res2 = llm.call_llm("system prompt", "user prompt")
    assert res2 == '{"result": "ok"}'
    assert mock_client.converse.call_count == 1  # Unchanged
    assert llm.get_token_usage()["calls"] == 1  # Unchanged

    # 3. Third call with different model -> Cache key changes -> Converse called again
    mock_client.converse.return_value = {
        "output": {"message": {"content": [{"text": '{"result": "model2"}'}]}},
        "usage": {"inputTokens": 10, "outputTokens": 5},
    }
    res3 = llm.call_llm("system prompt", "user prompt", model_id="different-model")
    assert res3 == '{"result": "model2"}'
    assert mock_client.converse.call_count == 2
    usage = llm.get_token_usage()
    assert usage["total_input_tokens"] == 52
    assert usage["total_output_tokens"] == 23
    assert usage["calls"] == 2


def test_no_cache_flag_bypasses_cache(monkeypatch):
    mock_boto3 = MagicMock()
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client

    mock_client.converse.return_value = {
        "output": {"message": {"content": [{"text": "fresh response"}]}},
        "usage": {"inputTokens": 5, "outputTokens": 5},
    }

    monkeypatch.setattr("boto3.client", mock_boto3.client)
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")
    monkeypatch.setenv("AWS_ARCH_NO_CACHE", "1")

    llm.call_llm("sys", "user")
    llm.call_llm("sys", "user")
    assert mock_client.converse.call_count == 2


def test_access_denied_exception_handling(monkeypatch):
    mock_client = MagicMock()
    mock_client.converse.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
        "Converse",
    )
    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: mock_client)
    monkeypatch.setenv("BEDROCK_MODEL_ID", "denied-model")

    with pytest.raises(RuntimeError) as exc:
        llm.call_llm("sys", "user")
    assert "Access Denied for Bedrock model 'denied-model'" in str(exc.value)
    assert "bedrock:InvokeModel" in str(exc.value)


def test_missing_credentials_handling(monkeypatch):
    mock_client = MagicMock()
    mock_client.converse.side_effect = NoCredentialsError()
    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: mock_client)
    monkeypatch.setenv("BEDROCK_MODEL_ID", "cred-model")

    with pytest.raises(RuntimeError) as exc:
        llm.call_llm("sys", "user")
    assert "AWS credentials not found" in str(exc.value)
