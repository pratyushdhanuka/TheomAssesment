import json
import os
from typing import Dict, Any, Optional
from .ISnapshotStore import ISnapshotStore


class S3SnapshotStore(ISnapshotStore):
    """A simulated S3-backed snapshot store.

    This implementation writes snapshot files to a local directory that acts
    as a stand-in for remote storage. It avoids adding an external dependency
    (like boto3) while keeping the same interface; it can be replaced with a
    real S3 implementation later.
    """

    def __init__(self, bucket_name: str = "s3_snapshots", directory: str = "s3_bucket"):
        self.bucket_name = bucket_name
        self.directory = os.path.join(directory, bucket_name)
        os.makedirs(self.directory, exist_ok=True)

    def _key_path(self, node_id: str) -> str:
        return os.path.join(self.directory, f"{node_id}.json")

    def save_snapshot(self, node_id: str, data: Dict[str, Any]) -> None:
        path = self._key_path(node_id)
        with open(path, "w") as f:
            json.dump(data, f)

    def load_snapshot(self, node_id: str) -> Optional[Dict[str, Any]]:
        path = self._key_path(node_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
