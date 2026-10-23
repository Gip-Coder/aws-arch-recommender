import json
from pathlib import Path
import yaml
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[2]

def load_json(path):
    return json.loads(Path(path).read_text())

def load_catalogue():
    return yaml.safe_load((ROOT / "catalogue" / "catalogue.yaml").read_text())

def load_patterns():
    return yaml.safe_load((ROOT / "catalogue" / "patterns.yaml").read_text())["patterns"]

def check_schema(obj, name):
    validate(obj, load_json(ROOT / "schemas" / f"{name}.schema.json"))
