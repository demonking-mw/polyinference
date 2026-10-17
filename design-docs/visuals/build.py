"""Build two offline, self-contained design readers. No third-party packages."""
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def main() -> None:
    content = runpy.run_path(str(HERE / "content.py"))["CONTENT"]
    content["provenance"] = [
        {"path": name, "digest": hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}
        for name in (
            "design-docs/langgraph-agent/README.md",
            "design-docs/simplified-os/README.md",
            "design-docs/INTEGRATION_AUDIT.md",
            "design-docs/polyinference-design/polyinference-agent-design-merged.json",
        )
    ]
    chinese = json.loads((HERE / "zh-CN.json").read_text(encoding="utf-8"))
    chinese["content"]["provenance"] = content["provenance"]
    content["locales"] = {"zh-CN": chinese["content"]}
    content["ui_zh"] = chinese["ui"]
    template = (HERE / "template.html").read_text(encoding="utf-8")
    css = (HERE / "atlas.css").read_text(encoding="utf-8")
    script = (HERE / "atlas.js").read_text(encoding="utf-8")
    for page in ("agent", "os"):
        data = dict(content, page=page)
        encoded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
        result = template.replace("__TITLE__", content[page]["title"])
        result = result.replace("__CSS__", css).replace("__DATA__", encoded).replace("__SCRIPT__", script)
        destination = HERE / f"{page}-design.html"
        destination.write_text(result, encoding="utf-8", newline="\n")
        print(f"Built {destination.name}: {len(result.encode('utf-8')):,} bytes")


if __name__ == "__main__":
    main()
