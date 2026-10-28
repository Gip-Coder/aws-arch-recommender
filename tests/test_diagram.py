"""Tests for aws_arch.diagram."""
import sys
from pathlib import Path

# Ensure src/ is on sys.path for test collection
SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from unittest import mock

import pytest
from diagrams import Node

from aws_arch.common import ROOT, load_catalogue, load_json
from aws_arch.diagram import FALLBACK_SERVICES, SERVICE_MAP, _render_diagrams, render, to_dot

ARCH_EXAMPLE = load_json(ROOT / "examples/ecommerce_architecture.json")


def test_mapping_covers_every_catalogue_service():
    """Ensure every service in catalogue.yaml is in SERVICE_MAP and list fallbacks."""
    cat = load_catalogue()
    catalogue_services = cat.get("services", {})
    assert len(catalogue_services) > 0

    missing_from_map = []
    for svc_name in catalogue_services:
        if svc_name not in SERVICE_MAP:
            missing_from_map.append(svc_name)
        else:
            cls = SERVICE_MAP[svc_name]
            assert issubclass(cls, Node), f"{svc_name} mapped to {cls}, not a subclass of Node"

    assert not missing_from_map, f"Services missing from SERVICE_MAP: {missing_from_map}"

    # Print / record services that fell back to generic Node (required by spec)
    print(f"\nFallback services using generic Node: {FALLBACK_SERVICES}")
    for svc in FALLBACK_SERVICES:
        assert svc in catalogue_services


def test_unknown_service_type_does_not_raise(tmp_path):
    """Unknown service types fall back to a generic labelled node without crashing."""
    arch_unknown = {
        "services": [
            {"id": "custom1", "type": "TotallyUnknownService", "role": "secret-sauce"},
            {"id": "app", "type": "EC2AutoScalingGroup", "role": "web"},
        ],
        "connections": [{"from": "custom1", "to": "app"}],
    }

    # Ensure DOT generation works
    dot_output = to_dot(arch_unknown)
    assert 'TotallyUnknownService\\n(secret-sauce)' in dot_output

    # Mock Diagram.render to avoid requiring Graphviz binary
    def mock_render(diag_self):
        Path(diag_self.filename).touch()
        Path(f"{diag_self.filename}.png").touch()

    with mock.patch("diagrams.Diagram.render", mock_render):
        # Should not raise
        _render_diagrams(arch_unknown, tmp_path / "test_unknown")


def test_dot_fallback_when_dot_missing(tmp_path, capsys):
    """When Graphviz dot is missing, fallback to DOT, write guidance to stderr, keep stdout clean."""
    out_base = tmp_path / "diagram"

    with mock.patch("shutil.which", return_value=None):
        outputs = render(ARCH_EXAMPLE, out_base)

    # Returned only .dot file
    assert len(outputs) == 1
    dot_file = outputs[0]
    assert dot_file.suffix == ".dot"
    assert dot_file.exists()
    assert not (tmp_path / "diagram.png").exists()

    # Capture output
    captured = capsys.readouterr()
    assert captured.out == "", "Nothing should be printed to stdout on missing Graphviz"

    stderr = captured.err
    assert "Graphviz 'dot' executable was not found on PATH" in stderr
    assert "winget install Graphviz.Graphviz" in stderr
    assert "choco install graphviz" in stderr
    assert r"C:\Program Files\Graphviz\bin" in stderr
    assert r"C:\Program Files (x86)\Graphviz\bin" in stderr


def test_lazy_diagrams_import_fallback(tmp_path, capsys):
    """When diagrams is not installed or import fails, fallback to DOT without raising."""
    out_base = tmp_path / "diagram_no_diagrams"

    with mock.patch.dict("sys.modules", {"diagrams": None}):
        with mock.patch("shutil.which", return_value="C:\\Program Files\\Graphviz\\bin\\dot.exe"):
            outputs = render(ARCH_EXAMPLE, out_base)

    assert len(outputs) == 1
    assert outputs[0].suffix == ".dot"
    assert outputs[0].exists()
    captured = capsys.readouterr()
    assert "package is not installed" in captured.err


def test_successful_render_returns_both_files_no_viewer(tmp_path):
    """When dot is present, render returns [dot_path, png_path] without opening viewer."""
    out_base = tmp_path / "diagram"

    def mock_render(diag_self):
        assert diag_self.show is False, "show must be False so no image viewer opens"
        assert diag_self.dot.graph_attr.get("rankdir") == "LR", "direction must be LR"
        assert diag_self.outformat == "png", "outformat must be png"
        Path(diag_self.filename).touch()
        Path(f"{diag_self.filename}.png").touch()

    with mock.patch("shutil.which", return_value="C:\\Program Files\\Graphviz\\bin\\dot.exe"):
        with mock.patch("diagrams.Diagram.render", mock_render):
            outputs = render(ARCH_EXAMPLE, out_base)

    assert len(outputs) == 2
    assert outputs[0] == tmp_path / "diagram.dot"
    assert outputs[1] == tmp_path / "diagram.png"
    assert outputs[0].exists()
    assert outputs[1].exists()


def test_identical_input_gives_identical_sorted_node_and_edge_order(tmp_path):
    """Different ordering of services and connections in JSON produces identical DOT output."""
    arch_shuffled = {
        "services": [
            {"id": "db", "type": "RDS_MultiAZ", "role": "relational data store"},
            {"id": "app", "type": "EC2AutoScalingGroup", "role": "application tier"},
            {"id": "cdn", "type": "CloudFront", "role": "content delivery"},
            {"id": "alb", "type": "ApplicationLoadBalancer", "role": "traffic distribution"},
        ],
        "connections": [
            {"from": "app", "to": "db"},
            {"from": "cdn", "to": "alb"},
            {"from": "alb", "to": "app"},
        ],
    }

    dot1 = to_dot(ARCH_EXAMPLE)
    dot2 = to_dot(arch_shuffled)
    assert dot1 == dot2, "DOT output should be strictly identical regardless of input order"

    # Also verify node and cluster ordering inside Diagram
    sources = []

    def mock_capture(diag_self):
        sources.append(diag_self.dot.source)
        Path(diag_self.filename).touch()
        Path(f"{diag_self.filename}.png").touch()

    with mock.patch("diagrams.Diagram.render", mock_capture):
        _render_diagrams(ARCH_EXAMPLE, tmp_path / "d1")
        _render_diagrams(arch_shuffled, tmp_path / "d2")

    assert len(sources) == 2
    assert sources[0] == sources[1], "Generated diagrams graph source must be identical"


def test_rds_multiaz_node_label(tmp_path):
    """RDS_MultiAZ is labelled 'RDS_MultiAZ\n(relational data store)'."""
    dot = to_dot(ARCH_EXAMPLE)
    assert 'RDS_MultiAZ\\n(relational data store)' in dot
