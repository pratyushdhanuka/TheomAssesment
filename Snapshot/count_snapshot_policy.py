from .ISnapshotPolicy import ISnapshotPolicy
import threading

class CountSnapshotPolicy(ISnapshotPolicy):
    def __init__(self, threshold: int = 100):
        self.threshold = max(1, int(threshold))
        self._count = 0
        self._lock = threading.Lock()

    def on_write(self) -> bool:
        with self._lock:
            self._count += 1
            return self._count >= self.threshold

    def should_snapshot_now(self) -> bool:
        with self._lock:
            return self._count >= self.threshold

    def mark_snapshot_completed(self) -> None:
        with self._lock:
            self._count = 0
