"""Deterministic diagram: Architecture JSON -> diagrams.aws.* (or Graphviz DOT fallback)."""
import shutil
import sys
from pathlib import Path


def _load_service_map() -> tuple[dict[str, type], list[str]]:
    """Build mapping from catalogue service types to diagrams classes.

    Verifies each class exists by importing it. If an import fails, uses
    generic Node and tracks the fallback.
    """
    try:
        from diagrams import Node
    except ImportError:
        class Node:  # type: ignore
            def __init__(self, label: str):
                self.label = label

    mapping: dict[str, type] = {}
    fallback: list[str] = []

    service_targets = {
        "CloudFront": ("diagrams.aws.network", "CloudFront"),
        "Route53": ("diagrams.aws.network", "Route53"),
        "ApplicationLoadBalancer": ("diagrams.aws.network", "ALB"),
        "APIGateway": ("diagrams.aws.network", "APIGateway"),
        "EC2AutoScalingGroup": ("diagrams.aws.compute", "EC2AutoScaling"),
        "ECSFargate": ("diagrams.aws.compute", "Fargate"),
        "Lambda": ("diagrams.aws.compute", "Lambda"),
        "RDS": ("diagrams.aws.database", "RDS"),
        # TODO: diagrams lacks dedicated Multi-AZ node icon; uses official RDS node
        "RDS_MultiAZ": ("diagrams.aws.database", "RDS"),
        "DynamoDB": ("diagrams.aws.database", "Dynamodb"),
        "ElastiCache": ("diagrams.aws.database", "ElastiCache"),
        "S3": ("diagrams.aws.storage", "S3"),
        "SQS": ("diagrams.aws.integration", "SQS"),
        "Cognito": ("diagrams.aws.security", "Cognito"),
        "Bedrock": ("diagrams.aws.ml", "Bedrock"),
        "CloudWatch": ("diagrams.aws.management", "Cloudwatch"),
        "IAM": ("diagrams.aws.security", "IAM"),
    }

    for svc_type, (mod_path, cls_name) in service_targets.items():
        cls = None
        try:
            mod = __import__(mod_path, fromlist=[cls_name])
            cls = getattr(mod, cls_name, None)
        except (ImportError, AttributeError):
            cls = None

        if cls is not None:
            mapping[svc_type] = cls
        else:
            # TODO: diagrams class not found for {svc_type}; using generic Node
            mapping[svc_type] = Node
            fallback.append(svc_type)

    return mapping, fallback


SERVICE_MAP, FALLBACK_SERVICES = _load_service_map()


def print_graphviz_missing_guidance() -> None:
    msg = (
        "Graphviz 'dot' executable was not found on PATH.\n"
        "To render architecture diagrams as PNG, please install Graphviz and add it to PATH:\n"
        "  - Windows (winget): winget install Graphviz.Graphviz\n"
        "  - Windows (choco):  choco install graphviz\n"
        "  - Download:         https://graphviz.org/download/\n"
        "Ensure Graphviz bin folder is on your PATH (e.g. C:\\Program Files\\Graphviz\\bin or "
        "C:\\Program Files (x86)\\Graphviz\\bin).\n"
        "Falling back to Graphviz DOT output."
    )
    print(msg, file=sys.stderr)


def to_dot(arch: dict) -> str:
    lines = ["digraph arch {", "  rankdir=LR; node [shape=box, style=rounded];"]
    for s in sorted(arch.get("services", []), key=lambda x: x["id"]):
        role = s.get("role", "")
        label = f"{s['type']}\\n({role})" if role else s["type"]
        lines.append(f'  "{s["id"]}" [label="{label}"];')
    for c in sorted(
        arch.get("connections", []),
        key=lambda x: (x.get("from", ""), x.get("to", ""), x.get("label", "")),
    ):
        label = f' [label="{c["label"]}"]' if c.get("label") else ""
        lines.append(f'  "{c["from"]}" -> "{c["to"]}"{label};')
    lines.append("}")
    return "\n".join(lines)


def _render_diagrams(arch: dict, out_stem: Path) -> None:
    from diagrams import Cluster, Diagram, Edge, Node

    catalogue = {}
    try:
        from .common import load_catalogue

        cat_data = load_catalogue()
        catalogue = cat_data.get("services", {})
    except Exception:
        pass

    clusters: dict[str, list[dict]] = {}
    for s in arch.get("services", []):
        cat = catalogue.get(s["type"], {}).get("category", "other")
        clusters.setdefault(cat, []).append(s)

    with Diagram("Architecture", show=False, direction="LR", outformat="png", filename=str(out_stem)):
        nodes = {}
        for cat_name in sorted(clusters.keys()):
            with Cluster(cat_name):
                for s in sorted(clusters[cat_name], key=lambda x: x["id"]):
                    node_cls = SERVICE_MAP.get(s["type"]) or Node
                    role = s.get("role", "")
                    label = f"{s['type']}\n({role})" if role else s["type"]
                    try:
                        nodes[s["id"]] = node_cls(label, nodeid=s["id"])
                    except TypeError:
                        nodes[s["id"]] = node_cls(label)

        for conn in sorted(
            arch.get("connections", []),
            key=lambda c: (c.get("from", ""), c.get("to", ""), c.get("label", "")),
        ):
            src = nodes.get(conn.get("from"))
            dst = nodes.get(conn.get("to"))
            if src and dst:
                label = conn.get("label")
                if label:
                    src >> Edge(label=label) >> dst
                else:
                    src >> dst


def render(arch: dict, out_base: Path) -> list[Path]:
    base_stem = out_base.parent / out_base.stem if out_base.suffix in (".dot", ".png") else out_base
    base_stem.parent.mkdir(parents=True, exist_ok=True)
    dot_path = Path(f"{base_stem}.dot")
    dot_path.write_text(to_dot(arch), encoding="utf-8")

    if not shutil.which("dot"):
        print_graphviz_missing_guidance()
        return [dot_path]

    try:
        from diagrams import Diagram
    except ImportError:
        print(
            "The 'diagrams' package is not installed. Falling back to Graphviz DOT output.",
            file=sys.stderr,
        )
        return [dot_path]

    png_path = Path(f"{base_stem}.png")
    try:
        _render_diagrams(arch, base_stem)
        return [dot_path, png_path]
    except Exception as err:
        print(
            f"Failed to render PNG diagram using diagrams ({err}). Falling back to Graphviz DOT output.",
            file=sys.stderr,
        )
        return [dot_path]
