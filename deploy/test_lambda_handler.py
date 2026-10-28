"""Local deterministic unit tests for the AWS Lambda handler.

Verifies mock pipeline execution, input validation, API Gateway format handling,
and Bedrock opt-in gating without network access or AWS credentials.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

# Add 'deploy' and 'src' to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "deploy") not in sys.path:
    sys.path.insert(0, str(ROOT / "deploy"))

from lambda_handler import lambda_handler


def test_lambda_handler_direct_valid_event():
    event = {"text": "Build a small e-commerce application"}
    response = lambda_handler(event)
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"

    body = json.loads(response["body"])
    assert body["valid"] is True
    assert body["mock_mode"] is True
    assert body["input_text"] == "Build a small e-commerce application"
    assert "execution_note" in body
    assert "services" in body
    assert "cost" in body
    assert "security" in body
    assert "assumptions" in body


def test_lambda_handler_apigateway_event():
    event = {
        "version": "2.0",
        "routeKey": "POST /recommend",
        "body": json.dumps({"text": "Create a high-availability web app"}),
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["valid"] is True
    assert body["input_text"] == "Create a high-availability web app"


def test_lambda_handler_apigateway_base64_event():
    raw_json = json.dumps({"text": "Batch processing with SQS"})
    b64_body = base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")
    event = {
        "body": b64_body,
        "isBase64Encoded": True,
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["input_text"] == "Batch processing with SQS"


def test_lambda_handler_missing_text():
    event = {"other_key": "value"}
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing required field: 'text'" in body["error"]


def test_lambda_handler_empty_text():
    event = {"text": "   "}
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "cannot be empty" in body["error"]


def test_lambda_handler_non_string_text():
    event = {"text": 12345}
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "must be a string" in body["error"]


def test_lambda_handler_invalid_json_body():
    event = {"body": "{invalid-json-syntax"}
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON syntax" in body["error"]


def test_lambda_handler_invalid_base64_body():
    event = {"body": "!!!not-valid-base64", "isBase64Encoded": True}
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid base64 encoding" in body["error"]


def test_lambda_handler_none_or_non_dict_event():
    assert lambda_handler(None)["statusCode"] == 400
    assert lambda_handler("just a string")["statusCode"] == 400
    assert lambda_handler([1, 2, 3])["statusCode"] == 400


def test_lambda_handler_bedrock_disabled_by_default(monkeypatch):
    monkeypatch.delenv("USE_BEDROCK", raising=False)
    event = {"text": "Test default mock pipeline"}
    response = lambda_handler(event)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["mock_mode"] is True


def test_lambda_handler_bedrock_opt_in_returns_501(monkeypatch):
    monkeypatch.setenv("USE_BEDROCK", "1")
    event = {"text": "Test Bedrock opt-in flag"}
    response = lambda_handler(event)
    assert response["statusCode"] == 501
    body = json.loads(response["body"])
    assert "Bedrock live integration is not implemented" in body["error"]
    assert body["implemented"] is False


def test_lambda_handler_no_network_or_aws_credentials_needed(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    monkeypatch.delenv("USE_BEDROCK", raising=False)

    event = {"text": "Completely offline test"}
    response = lambda_handler(event)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["valid"] is True
