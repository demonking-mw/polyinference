"""Generate/check the exact exported settings schema, including nested defaults."""

import argparse
import json
from pathlib import Path

from polyinference.config import AgentConfig
from polyinference.system_settings import RuntimeConfig

TARGET = Path(__file__).resolve().parents[1] / "docs/settings-schema.json"


def run(check=False):
    body = json.dumps({"RuntimeConfig": RuntimeConfig.model_json_schema(),
                       "AgentConfig": AgentConfig.model_json_schema()}, indent=2, sort_keys=True) + "\n"
    if check:
        if not TARGET.exists() or TARGET.read_text() != body:
            raise ValueError("Settings schema/default drift: run python scripts/settings_docs.py")
    else:
        TARGET.write_text(body)
    return "Settings schemas/defaults match the exported types."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    print(run(parser.parse_args().check))
