from typing import Dict, Any, Optional
from ..ISnapshotStore import ISnapshotStore


class InMemorySnapshotStore(ISnapshotStore):
    """A simple in-memory snapshot store useful for tests and fast local use.

    Snapshots are kept in a dictionary and are not persisted. This implementation
    satisfies the `ISnapshotStore` interface but does not provide durability.
    """

    def __init__(self):
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    def save_snapshot(self, node_id: str, data: Dict[str, Any]) -> None:
        # store a shallow copy to avoid accidental external mutation
        self._snapshots[node_id] = dict(data)

    def load_snapshot(self, node_id: str) -> Optional[Dict[str, Any]]:
        snap = self._snapshots.get(node_id)
        return dict(snap) if snap is not None else None
