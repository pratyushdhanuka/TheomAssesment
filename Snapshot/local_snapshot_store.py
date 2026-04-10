import json
import os
import tempfile
from typing import Dict, Any, Optional
from .ISnapshotStore import ISnapshotStore


class LocalSnapshotStore(ISnapshotStore):
    """Persist snapshots to the local filesystem.

    Snapshots are written atomically (write to a temp file and rename) to avoid
    producing partial files on crash.
    """

    def __init__(self, directory: str = "snapshots"):
        self.directory = directory
        os.makedirs(self.directory, exist_ok=True)

    def _path(self, node_id: str) -> str:
        return os.path.join(self.directory, f"{node_id}_snapshot.json")

    def save_snapshot(self, node_id: str, data: Dict[str, Any]) -> None:
        path = self._path(node_id)
        dirpath = os.path.dirname(path)
        os.makedirs(dirpath, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix=".tmp_snapshot_")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f)
                f.flush()
                os.fsync(f.fileno())
            # atomic replace
            os.replace(tmp_path, path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def load_snapshot(self, node_id: str) -> Optional[Dict[str, Any]]:
        path = self._path(node_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
