"""AWS Lambda entry point for the AWS Architecture Recommender.

Provides an HTTP API-compatible Lambda handler that accepts requirement text,
validates input, and executes the recommender pipeline in mock mode by default.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# Ensure repository root and 'src' are on sys.path so 'aws_arch' is importable
# whether running locally during testing or within an AWS Lambda deployment package.
_HANDLER_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _HANDLER_DIR.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from aws_arch.common import ROOT, load_json
    from aws_arch.pipeline import run_downstream
    _PIPELINE_AVAILABLE = True
    _PIPELINE_IMPORT_ERROR: str | None = None
except Exception as _import_err:  # pragma: no cover
    _PIPELINE_AVAILABLE = False
    _PIPELINE_IMPORT_ERROR = str(_import_err)


def _build_response(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Format standard API Gateway HTTP API proxy response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(payload, indent=2),
    }


def lambda_handler(event: dict[str, Any] | None, context: Any = None) -> dict[str, Any]:
    """AWS Lambda entry point.

    Accepts:
        Direct invocation event:
            {"text": "Build a small e-commerce application"}
        API Gateway HTTP API event:
            {"body": "{\"text\": \"Build a small e-commerce application\"}"}

    Returns:
        API Gateway HTTP response dictionary with 'statusCode', 'headers', and 'body'.
    """
    if event is None or not isinstance(event, dict):
        return _build_response(400, {"error": "Invalid event: expected a JSON object"})

    # Parse request body from direct payload or API Gateway proxy wrapper
    body: Any = event
    if "body" in event:
        raw_body = event["body"]
        if event.get("isBase64Encoded"):
            try:
                raw_body = base64.b64decode(raw_body).decode("utf-8")
            except Exception:
                return _build_response(400, {"error": "Invalid base64 encoding in request body"})

        if isinstance(raw_body, str):
            try:
                body = json.loads(raw_body)
            except Exception:
                return _build_response(400, {"error": "Invalid JSON syntax in request body"})
        elif isinstance(raw_body, dict):
            body = raw_body
        else:
            return _build_response(400, {"error": "Invalid body format in request"})

    if not isinstance(body, dict):
        return _build_response(400, {"error": "Request body must be a JSON object"})

    # Validate mandatory 'text' input
    if "text" not in body:
        return _build_response(400, {"error": "Missing required field: 'text'"})

    text = body["text"]
    if not isinstance(text, str):
        return _build_response(400, {"error": "Field 'text' must be a string"})

    stripped_text = text.strip()
    if not stripped_text:
        return _build_response(400, {"error": "Field 'text' cannot be empty or whitespace"})

    # Bedrock opt-in evaluation:
    # Live LLM inference is not implemented in this serverless release because
    # upstream 'src/aws_arch/llm.py' requires configurable model IDs and a writable
    # cache directory (Lambda root is read-only).
    if os.environ.get("USE_BEDROCK") == "1":
        return _build_response(
            501,
            {
                "error": (
                    "Bedrock live integration is not implemented in this serverless release. "
                    "Upstream modules require configurable model IDs and writable cache storage. "
                    "Leave USE_BEDROCK unset (or set to 0) to execute in mock mode."
                ),
                "implemented": False,
            },
        )

    # Verify pipeline module availability
    if not _PIPELINE_AVAILABLE:  # pragma: no cover
        return _build_response(
            500,
            {
                "error": "Pipeline modules unavailable in execution environment",
                "detail": _PIPELINE_IMPORT_ERROR,
            },
        )

    # Execute deterministic mock pipeline using a temporary directory
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            req = load_json(ROOT / "examples" / "ecommerce_requirement.json")
            arch = load_json(ROOT / "examples" / "ecommerce_architecture.json")
            report = run_downstream(req, arch, out_path)

        # Build honest response payload disclosing mock mode behavior
        result = dict(report)
        result["mock_mode"] = True
        result["input_text"] = stripped_text
        result["execution_note"] = (
            "Demonstration mock mode: returned canonical e-commerce reference architecture. "
            "Input prompt was validated successfully; dynamic requirement parsing requires "
            "Bedrock integration which is not configured in this release."
        )

        return _build_response(200, result)

    except Exception as exc:  # pragma: no cover
        return _build_response(
            500,
            {
                "error": "Internal pipeline execution error",
                "detail": str(exc),
            },
        )
