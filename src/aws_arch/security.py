"""Rule-based Well-Architected security and architecture checks."""
from collections import defaultdict


def _types(arch: dict) -> set[str]:
    return {s["type"] for s in arch.get("services", [])}


def _id_to_type(arch: dict) -> dict[str, str]:
    return {s["id"]: s["type"] for s in arch.get("services", [])}


def _ctrls(arch: dict) -> str:
    return " ".join(arch.get("security_controls", [])).lower()


def check_security(arch: dict, req: dict | None = None) -> list[dict]:
    """Evaluate deterministic Well-Architected checks across 5 pillars.

    Returns a list of finding dicts, each with keys:
    id, pillar, rule, severity, passed, recommendation.
    Handles req=None safely. No LLM calls, no network access.
    """
    t = _types(arch)
    id_map = _id_to_type(arch)
    ctrls = _ctrls(arch)
    req = req or {}

    findings: list[dict] = []

    def add(rule_id: str, pillar: str, rule: str, severity: str, ok: bool, fix: str) -> None:
        findings.append({
            "id": rule_id,
            "pillar": pillar,
            "rule": rule,
            "severity": severity,
            "passed": ok,
            "recommendation": None if ok else fix,
        })

    # ---------------------------------------------------------
    # Pillar 1: Security
    # ---------------------------------------------------------
    # SEC-01: Least-privilege IAM roles
    add(
        "SEC-01",
        "Security",
        "Least-privilege IAM roles declared",
        "high",
        "iam" in ctrls or "least-privilege" in ctrls or "IAM" in t,
        "Declare least-privilege IAM roles per component in security_controls.",
    )

    # SEC-02: Encryption at rest
    add(
        "SEC-02",
        "Security",
        "Encryption at rest declared",
        "high",
        "at rest" in ctrls or "encryption at rest" in ctrls,
        "Enable encryption at rest for data stores (S3, RDS, DynamoDB).",
    )

    # SEC-03: Encryption in transit
    add(
        "SEC-03",
        "Security",
        "Encryption in transit declared",
        "high",
        "transit" in ctrls or "tls" in ctrls or "https" in ctrls,
        "Enforce TLS/HTTPS encryption in transit across all endpoints.",
    )

    # SEC-04: S3 bucket public access restricted
    s3_present = "S3" in t
    s3_protected = (
        ("no public s3" in ctrls)
        or ("block public access" in ctrls)
        or ("cloudfront" in {x.lower() for x in t})
    )
    add(
        "SEC-04",
        "Security",
        "S3 bucket public access restricted",
        "high",
        (not s3_present) or s3_protected,
        "Enable S3 Block Public Access and restrict bucket access via CloudFront OAC.",
    )

    # SEC-05: Public entry point TLS / WAF protection
    public_entry_services = {"CloudFront", "ApplicationLoadBalancer", "APIGateway"}
    has_public_entry = bool(public_entry_services & t)
    entry_protected = any(term in ctrls for term in ["tls", "https", "waf", "transit"])
    add(
        "SEC-05",
        "Security",
        "Public entry point protected with TLS or WAF",
        "medium",
        (not has_public_entry) or entry_protected,
        "Configure TLS/HTTPS and consider AWS WAF on public-facing entry points (CloudFront, ALB, API Gateway).",
    )

    # SEC-06: Authentication service configured when required
    compliance = [str(c).lower() for c in req.get("security_compliance", [])]
    auth_required = any("auth" in c for c in compliance)
    has_auth = "Cognito" in t or "cognito" in ctrls or "auth" in ctrls
    add(
        "SEC-06",
        "Security",
        "Authentication service configured when required",
        "high",
        (not auth_required) or has_auth,
        "Add Amazon Cognito or specify an authentication control when compliance requires authentication.",
    )

    # SEC-07: Database isolated from direct public ingress
    db_types = {"RDS", "RDS_MultiAZ", "DynamoDB"}
    req_text = " ".join([
        str(req.get("app_type", "")),
        " ".join(req.get("assumptions", [])),
    ]).lower()
    public_db_requested = "public database" in req_text or "public-facing database" in req_text or "public db" in req_text

    direct_public_db_connection = False
    for c in arch.get("connections", []):
        src_type = id_map.get(c.get("from", ""))
        dst_type = id_map.get(c.get("to", ""))
        if src_type in {"CloudFront", "APIGateway"} and dst_type in db_types:
            direct_public_db_connection = True
            break

    add(
        "SEC-07",
        "Security",
        "Database isolated from direct public ingress",
        "high",
        (not public_db_requested) and (not direct_public_db_connection),
        "Keep databases in private subnets behind compute tiers; never expose directly to public networks.",
    )

    # ---------------------------------------------------------
    # Pillar 2: Reliability
    # ---------------------------------------------------------
    # REL-01: Multi-AZ database for high availability
    is_high_avail = req.get("availability") == "high" or not req
    has_single_rds = "RDS" in t and "RDS_MultiAZ" not in t
    add(
        "REL-01",
        "Reliability",
        "Database is Multi-AZ for high availability",
        "high",
        not (is_high_avail and has_single_rds),
        "Use Multi-AZ RDS deployment for automated failover and high availability.",
    )

    # REL-02: Compute tier auto-scaling
    scalable_compute = {"EC2AutoScalingGroup", "ECSFargate", "Lambda"}
    has_compute = bool({"EC2AutoScalingGroup", "ECSFargate", "Lambda", "EC2"} & t)
    compute_scalable = bool(scalable_compute & t)
    users = req.get("expected_users", 0)
    high_traffic = users >= 50000 or req.get("traffic_pattern") in {"steady", "spiky"}
    compute_ok = (not has_compute) or (not high_traffic) or compute_scalable
    add(
        "REL-02",
        "Reliability",
        "Compute tier auto-scaling configured for elasticity",
        "medium",
        compute_ok,
        "Use Auto Scaling Groups or serverless compute to handle load fluctuations.",
    )

    # REL-03: Decouple spiky workloads with message queue
    is_spiky = req.get("traffic_pattern") == "spiky"
    has_queue = "SQS" in t or any(w in ctrls for w in ["sqs", "queue", "buffer", "decoupled"])
    add(
        "REL-03",
        "Reliability",
        "Decouple spiky workloads with message queue",
        "medium",
        (not is_spiky) or has_queue,
        "Introduce SQS message queues to buffer spiky workloads and prevent compute overload.",
    )

    # ---------------------------------------------------------
    # Pillar 3: Cost Optimization
    # ---------------------------------------------------------
    # COST-01: Avoid over-provisioned design for minimal budget
    is_minimal_budget = req.get("budget_sensitivity") == "minimise"
    heavy_combo = {"EC2AutoScalingGroup", "ApplicationLoadBalancer", "RDS_MultiAZ"}.issubset(t)
    add(
        "COST-01",
        "Cost Optimization",
        "Avoid over-provisioned design for minimal budget",
        "medium",
        not (is_minimal_budget and heavy_combo),
        "Consider serverless compute (Lambda) and DynamoDB or single-AZ RDS to reduce baseline costs for minimal budgets.",
    )

    # COST-02: Static asset offloading via CDN or object storage
    app_type_str = str(req.get("app_type", "")).lower()
    is_web = any(w in app_type_str for w in ["web", "e-commerce", "ecommerce"]) or arch.get("pattern") in {
        "three_tier_web",
        "serverless_web",
    }
    has_static_offload = bool({"CloudFront", "S3"} & t)
    add(
        "COST-02",
        "Cost Optimization",
        "Static asset offloading via CDN or object storage",
        "low",
        (not is_web) or has_static_offload,
        "Use CloudFront caching or S3 storage for static assets to reduce compute origin and egress costs.",
    )

    # ---------------------------------------------------------
    # Pillar 4: Performance Efficiency
    # ---------------------------------------------------------
    # PERF-01: Content delivery network configured for low latency
    needs_cdn = req.get("performance") == "low-latency" or users >= 50000
    has_cdn = "CloudFront" in t
    add(
        "PERF-01",
        "Performance Efficiency",
        "Content delivery network configured for low latency",
        "medium",
        (not needs_cdn) or has_cdn,
        "Deploy CloudFront edge locations to reduce latency and accelerate content delivery.",
    )

    # PERF-02: Database read caching considered for high scale
    extreme_users = users >= 500000
    has_rds = bool({"RDS", "RDS_MultiAZ"} & t)
    has_cache = "ElastiCache" in t or "cache" in ctrls
    add(
        "PERF-02",
        "Performance Efficiency",
        "Database caching for high-scale relational workloads",
        "low",
        not (extreme_users and has_rds and not has_cache),
        "Add ElastiCache (Redis/Memcached) in front of RDS to offload read-heavy database traffic.",
    )

    # ---------------------------------------------------------
    # Pillar 5: Operational Excellence
    # ---------------------------------------------------------
    # OPS-01: Centralized monitoring and logging configured
    has_ops = "CloudWatch" in t or any(w in ctrls for w in ["cloudwatch", "monitoring", "logging"])
    add(
        "OPS-01",
        "Operational Excellence",
        "Centralized monitoring and logging configured",
        "medium",
        has_ops,
        "Add Amazon CloudWatch to collect metrics, logs, and configure alarms for all components.",
    )

    return findings


def summarize_security(findings: list[dict]) -> dict:
    """Summarize security findings with total, passed, failed, and counts per pillar."""
    total = len(findings)
    passed = sum(1 for f in findings if f["passed"])
    failed = total - passed
    pass_rate = round(passed / total, 3) if total > 0 else 1.0

    by_pillar: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
    for f in findings:
        p = f["pillar"]
        by_pillar[p]["total"] += 1
        if f["passed"]:
            by_pillar[p]["passed"] += 1
        else:
            by_pillar[p]["failed"] += 1

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "by_pillar": dict(by_pillar),
    }
