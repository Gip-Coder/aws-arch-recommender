"""Rule-based security / Well-Architected checks. Each rule returns a finding or None."""
def _types(arch):
    return {s.get("type") for s in (arch.get("services") or []) if isinstance(s, dict) and "type" in s}

def check_security(arch: dict, req: dict | None = None) -> list[dict]:
    raw_ctrls = arch.get("security_controls") or []
    ctrls = " ".join(str(c) for c in raw_ctrls).lower()
    t = _types(arch)
    out = []
    def add(pillar, rule, ok, fix):
        out.append({"pillar": pillar, "rule": rule, "passed": ok, "recommendation": None if ok else fix})
    add("Security", "Least-privilege IAM roles declared", "iam" in ctrls, "Add scoped IAM roles per component.")
    add("Security", "Encryption at rest declared", "at rest" in ctrls, "Enable encryption at rest (S3, RDS, EBS, DynamoDB).")
    add("Security", "Encryption in transit declared", "transit" in ctrls or "tls" in ctrls, "Enforce TLS/HTTPS end to end.")
    if "S3" in t:
        add("Security", "S3 not publicly exposed", "no public s3" in ctrls or "cloudfront" in {x.lower() for x in t}, "Enable Block Public Access; serve via CloudFront OAC.")
    if req and req.get("availability") == "high":
        add("Reliability", "Database is Multi-AZ for high availability",
            ("RDS" not in t) or ("RDS_MultiAZ" in t), "Use Multi-AZ RDS for high availability.")
    return out
