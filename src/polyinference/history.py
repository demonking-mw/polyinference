"""A rolling archive of the same JSON snapshots offered by UI Save."""

from __future__ import annotations

import json
import logging
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .snapshots import export_run

logger = logging.getLogger(__name__)


def prune_history(directory, now=None):
    """Only remove archive files older than 30 days; never traverse run state."""
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=30)
    for path in Path(directory).glob("*.json"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            # The UTC completion time is in the name, so copying or touching a
            # snapshot cannot extend its retention period.
            completed = datetime.strptime(path.stem.split("-", 1)[0], "%Y%m%dT%H%M%S%fZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        if completed < cutoff:
            path.unlink(missing_ok=True)


async def save_run_history(config, directory=None, metadata=None):
    """Archive every finished invocation, including failures and resumed runs.

    Archiving errors are logged without replacing the agent's result or error.
    Cleanup still runs if snapshot creation fails.
    """
    directory = Path(directory) if directory is not None else Path.cwd() / ".polyinference" / "history"
    now = datetime.now(timezone.utc)
    metadata = metadata or {
        "id": uuid.uuid4().hex[:12],
        "state": str(config.state_path),
        "repository": config.repository,
        "created_at": now.isoformat(),
        "finished_at": now.isoformat(),
        "error": None,
    }
    temporary = None
    try:
        if config is None:
            config_path = Path(metadata["state"]).parent / "config.json"
            configuration = json.loads(config_path.read_text()) if config_path.is_file() else {}
        else:
            configuration = config.model_dump(mode="json")
        document = await export_run(metadata, configuration)
        directory.mkdir(parents=True, exist_ok=True)
        name = now.strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex + ".json"
        # A unique temporary file also allows simultaneous CLI completions.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(document, stream, indent=2)
        temporary.replace(directory / name)
    except Exception:
        logger.exception("Could not save run history in %s", directory)
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logger.exception("Could not remove temporary history file %s", temporary)
        try:
            prune_history(directory)
        except OSError:
            logger.exception("Could not prune run history in %s", directory)
