"""Deterministic diagram: Architecture JSON -> Graphviz DOT (-> PNG if `dot` is installed)."""
import shutil, subprocess
from pathlib import Path

def to_dot(arch: dict) -> str:
    lines = ["digraph arch {", "  rankdir=LR; node [shape=box, style=rounded];"]
    for s in arch["services"]:
        lines.append(f'  "{s["id"]}" [label="{s["type"]}\\n({s["role"]})"];')
    for c in arch["connections"]:
        label = f' [label="{c["label"]}"]' if c.get("label") else ""
        lines.append(f'  "{c["from"]}" -> "{c["to"]}"{label};')
    lines.append("}")
    return "\n".join(lines)

def render(arch: dict, out_base: Path) -> list[Path]:
    dot_path = Path(f"{out_base}.dot"); dot_path.write_text(to_dot(arch))
    outputs = [dot_path]
    if shutil.which("dot"):
        png = Path(f"{out_base}.png")
        subprocess.run(["dot", "-Tpng", str(dot_path), "-o", str(png)], check=True)
        outputs.append(png)
    return outputs
