import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aws_arch.common import ROOT, load_json, check_schema
from aws_arch.validator import validate_architecture
from aws_arch.security import check_security
from aws_arch.cost import estimate_cost

ARCH = load_json(ROOT / "examples/ecommerce_architecture.json")
REQ = load_json(ROOT / "examples/ecommerce_requirement.json")

def test_examples_match_schema():
    check_schema(ARCH, "architecture"); check_schema(REQ, "requirement")

def test_valid_architecture_has_no_errors():
    assert validate_architecture(ARCH) == []

def test_hallucinated_service_rejected():
    bad = {**ARCH, "services": ARCH["services"] + [{"id": "x", "type": "AWSMagicBox", "role": "?"}]}
    assert any("not in the curated catalogue" in e for e in validate_architecture(bad))

def test_orphan_detected():
    bad = {**ARCH, "services": ARCH["services"] + [{"id": "q", "type": "SQS", "role": "queue"}]}
    assert any("Orphaned" in e for e in validate_architecture(bad))

def test_invalid_connection_rejected():
    bad = {**ARCH, "connections": ARCH["connections"] + [{"from": "db", "to": "app"}]}
    assert any("not an allowed connection" in e for e in validate_architecture(bad))

def test_cost_range_ordered():
    c = estimate_cost(ARCH)
    if c["monthly_usd_low"] is not None and c["monthly_usd_high"] is not None:
        assert c["monthly_usd_low"] <= c["monthly_usd_high"]
    else:
        assert c["status"] == "incomplete"

def test_security_all_pass_for_example():
    assert all(f["passed"] for f in check_security(ARCH, REQ))

def test_pipeline_returns_structured_error_on_schema_violation(tmp_path):
    from aws_arch.pipeline import run_downstream
    bad_arch = {'services': []}
    res = run_downstream(REQ, bad_arch, tmp_path)
    assert res['valid'] is False
    assert any('Schema validation error' in err for err in res['errors'])

def test_pipeline_free_tier_mode_in_architecture_schema():
    arch_with_mode = {**ARCH, 'free_tier_mode': 'consumed', 'pricing_options': {'include_support': False}}
    check_schema(arch_with_mode, 'architecture')

def test_pipeline_run_downstream_with_none_req_and_none_assumptions(tmp_path):
    from aws_arch.pipeline import run_downstream
    arch_no_assump = {k: v for k, v in ARCH.items() if k != 'assumptions'}
    res = run_downstream(None, arch_no_assump, tmp_path)
    assert res['valid'] is True
    assert isinstance(res['assumptions'], list)
    assert (tmp_path / 'report.json').exists()

def test_validator_duplicate_service_ids():
    bad = {
        'services': [
            {'id': 'svc1', 'type': 'S3', 'role': 'storage'},
            {'id': 'svc1', 'type': 'CloudFront', 'role': 'cdn'}
        ],
        'connections': [{'from': 'svc1', 'to': 'svc1'}]
    }
    errors = validate_architecture(bad)
    assert 'Duplicate service ids' in errors

def test_validator_defensive_against_missing_or_malformed_keys():
    assert 'Architecture must contain a list of \'services\'' in validate_architecture({})
    bad_entries = {
        'services': ['not-a-dict', {'id': 's1'}],
        'connections': ['not-a-dict', {'from': 's1'}]
    }
    errors = validate_architecture(bad_entries)
    assert any('Invalid service definition' in e for e in errors)
    assert any('Invalid connection definition' in e for e in errors)

def test_security_handles_none_and_non_string_controls():
    arch_with_none = {**ARCH, 'security_controls': None}
    findings = check_security(arch_with_none, REQ)
    assert isinstance(findings, list)
    arch_with_int = {**ARCH, 'security_controls': [123, 'iam', 'tls', 'at rest', 'no public s3']}
    findings2 = check_security(arch_with_int, REQ)
    assert all(f['passed'] for f in findings2)

def test_security_flags_missing_controls_and_single_az_rds():
    insecure_arch = {
        'services': [
            {'id': 'app', 'type': 'EC2AutoScalingGroup', 'role': 'app'},
            {'id': 'db', 'type': 'RDS', 'role': 'database'}
        ],
        'connections': [{'from': 'app', 'to': 'db'}],
        'security_controls': []
    }
    high_avail_req = {'availability': 'high'}
    findings = check_security(insecure_arch, high_avail_req)
    unpassed = [f for f in findings if not f['passed']]
    unpassed_rules = {f['rule'] for f in unpassed}
    assert 'Least-privilege IAM roles declared' in unpassed_rules
    assert 'Encryption at rest declared' in unpassed_rules
    assert 'Encryption in transit declared' in unpassed_rules
    assert 'Database is Multi-AZ for high availability' in unpassed_rules

def test_security_standalone_s3_requires_protection():
    s3_alone = {
        'services': [{'id': 'bucket', 'type': 'S3', 'role': 'storage'}],
        'connections': [],
        'security_controls': ['iam', 'at rest', 'transit']
    }
    findings = check_security(s3_alone, {})
    s3_finding = next(f for f in findings if f['rule'] == 'S3 not publicly exposed')
    assert s3_finding['passed'] is False

    s3_protected = {
        'services': [{'id': 'bucket', 'type': 'S3', 'role': 'storage'}],
        'connections': [],
        'security_controls': ['iam', 'at rest', 'transit', 'no public s3']
    }
    findings_prot = check_security(s3_protected, {})
    assert next(f for f in findings_prot if f['rule'] == 'S3 not publicly exposed')['passed'] is True

def test_pattern_static_site_cdn(tmp_path):
    from aws_arch.pipeline import run_downstream
    arch = {
        'pattern': 'static_site_cdn',
        'services': [
            {'id': 'cdn', 'type': 'CloudFront', 'role': 'cdn', 'rationale': 'Edge caching'},
            {'id': 'storage', 'type': 'S3', 'role': 'storage', 'rationale': 'Static assets'}
        ],
        'connections': [{'from': 'cdn', 'to': 'storage'}],
        'security_controls': ['iam', 'at rest', 'tls', 'no public s3'],
        'assumptions': ['Static SPA application']
    }
    req = {
        'app_type': 'Static Web Application',
        'expected_users': 50000,
        'traffic_pattern': 'steady',
        'availability': 'standard',
        'budget_sensitivity': 'minimise'
    }
    check_schema(arch, 'architecture')
    check_schema(req, 'requirement')
    res = run_downstream(req, arch, tmp_path / 'static')
    assert res['valid'] is True
    assert res['cost']['status'] == 'complete'
    assert res['cost']['monthly_usd_low'] <= res['cost']['monthly_usd_high']
    assert all(f['passed'] for f in res['security'])

def test_pattern_serverless_rest_api(tmp_path):
    from aws_arch.pipeline import run_downstream
    arch = {
        'pattern': 'serverless_rest_api',
        'services': [
            {'id': 'auth', 'type': 'Cognito', 'role': 'auth', 'rationale': 'User pool auth'},
            {'id': 'api', 'type': 'APIGateway', 'role': 'api gateway', 'rationale': 'REST endpoints'},
            {'id': 'compute', 'type': 'Lambda', 'role': 'serverless logic', 'rationale': 'Execution environment'},
            {'id': 'db', 'type': 'DynamoDB', 'role': 'data store', 'rationale': 'NoSQL persistence'}
        ],
        'connections': [
            {'from': 'api', 'to': 'auth'},
            {'from': 'api', 'to': 'compute'},
            {'from': 'compute', 'to': 'db'}
        ],
        'security_controls': ['iam', 'at rest', 'tls'],
        'assumptions': ['Spiky traffic API']
    }
    req = {
        'app_type': 'Serverless API',
        'expected_users': 20000,
        'traffic_pattern': 'spiky',
        'availability': 'high',
        'budget_sensitivity': 'minimise'
    }
    check_schema(arch, 'architecture')
    check_schema(req, 'requirement')
    res = run_downstream(req, arch, tmp_path / 'serverless')
    assert res['valid'] is True
    assert res['cost']['status'] == 'complete'
    assert res['cost']['monthly_usd_low'] <= res['cost']['monthly_usd_high']
    assert all(f['passed'] for f in res['security'])

def test_pattern_batch_pipeline(tmp_path):
    from aws_arch.pipeline import run_downstream
    arch = {
        'pattern': 'batch_pipeline',
        'services': [
            {'id': 'landing', 'type': 'S3', 'role': 'raw ingestion', 'rationale': 'Incoming file landing'},
            {'id': 'queue', 'type': 'SQS', 'role': 'job queue', 'rationale': 'Decouple processing'},
            {'id': 'worker', 'type': 'Lambda', 'role': 'batch processing', 'rationale': 'Process items'},
            {'id': 'store', 'type': 'DynamoDB', 'role': 'metadata store', 'rationale': 'Processed records'}
        ],
        'connections': [
            {'from': 'queue', 'to': 'worker'},
            {'from': 'worker', 'to': 'store'},
            {'from': 'worker', 'to': 'landing'}
        ],
        'security_controls': ['iam', 'at rest', 'tls', 'no public s3'],
        'assumptions': ['Asynchronous document intake']
    }
    req = {
        'app_type': 'Batch Processing Pipeline',
        'expected_users': 1000,
        'traffic_pattern': 'spiky',
        'availability': 'standard',
        'budget_sensitivity': 'moderate'
    }
    check_schema(arch, 'architecture')
    check_schema(req, 'requirement')
    res = run_downstream(req, arch, tmp_path / 'batch')
    assert res['valid'] is True
    assert res['cost']['status'] == 'complete'
    assert res['cost']['monthly_usd_low'] <= res['cost']['monthly_usd_high']
    assert all(f['passed'] for f in res['security'])

def test_pattern_three_tier_web(tmp_path):
    from aws_arch.pipeline import run_downstream
    res = run_downstream(REQ, ARCH, tmp_path / 'threetier')
    assert res['valid'] is True
    assert res['cost']['monthly_usd_low'] == 84.58
    assert res['cost']['monthly_usd_high'] == 234.29
    assert all(f['passed'] for f in res['security'])
    assert (tmp_path / 'threetier' / 'report.json').exists()
