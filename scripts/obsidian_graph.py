"""Validate the shared Obsidian view and optionally apply it to this vault."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def notes_in(node):
    yield node["doc"]
    for child in node.get("children", []):
        yield from notes_in(child)


def path_query(query):
    if not query.startswith("path:/") or not query.endswith("/"):
        raise ValueError(f"Expected a path regex query: {query}")
    return re.compile(query[6:-1], re.IGNORECASE)


def validate(preset, canvas, notes):
    visible = path_query(preset["search"])
    groups = [path_query(group["query"]) for group in preset["colorGroups"]]
    for note in sorted(notes):
        if not visible.fullmatch(note):
            raise ValueError(f"Graph filter excludes {note}")
        if sum(bool(group.fullmatch(note)) for group in groups) != 1:
            raise ValueError(f"Expected exactly one graph color for {note}")

    node_ids = {node["id"] for node in canvas["nodes"]}
    if len(node_ids) != len(canvas["nodes"]):
        raise ValueError("Duplicate reading map node IDs")
    for node in canvas["nodes"]:
        targets = [node["file"]] if node["type"] == "file" else []
        if node["type"] == "text":
            targets = re.findall(r"\[\[([^#|\]]+)(?:[#|][^\]]*)?\]\]", node["text"])
        if missing := set(targets) - notes:
            raise ValueError(f"Unknown reading map notes: {sorted(missing)}")
    for edge in canvas["edges"]:
        if edge["fromNode"] not in node_ids or edge["toNode"] not in node_ids:
            raise ValueError(f"Unknown reading map edge endpoint: {edge['id']}")


def apply_preset(preset):
    directory = ROOT / ".obsidian"
    directory.mkdir(exist_ok=True)
    target = directory / "graph.json"
    current = read_json(target) if target.exists() else {}
    updated = {**current, **preset}
    if updated == current:
        print("Obsidian graph settings are already current.")
        return
    if target.exists():
        backup = target.with_name("graph.before-polyinference.json")
        if not backup.exists():
            shutil.copyfile(target, backup)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=directory, suffix=".tmp", delete=False,
    ) as output:
        json.dump(updated, output, indent=2)
        output.write("\n")
    temporary = Path(output.name)
    try:
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Applied the graph preset to {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate the shared files without editing the vault.")
    mode.add_argument("--apply", action="store_true", help="Apply after quitting Obsidian.")
    args = parser.parse_args()
    try:
        preset = read_json(ROOT / "docs/obsidian-graph.json")
        canvas = read_json(ROOT / "docs/reading-map.canvas")
        notes = set(notes_in(read_json(ROOT / "docs/file-tree.json")["root"]))
        validate(preset, canvas, notes)
        if args.apply:
            apply_preset(preset)
        print(f"Obsidian graph and reading map OK: {len(notes)} notes, {len(preset['colorGroups'])} groups.")
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Obsidian graph check failed: {exc}\n")


if __name__ == "__main__":
    main()
