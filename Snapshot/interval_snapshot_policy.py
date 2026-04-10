from .ISnapshotPolicy import ISnapshotPolicy
import threading
import time

class IntervalSnapshotPolicy(ISnapshotPolicy):
    def __init__(self, interval_seconds: float = 30.0):
        self.interval = max(0.1, float(interval_seconds))
        self._last_snapshot = time.monotonic()
        self._lock = threading.Lock()

    def on_write(self) -> bool:
        # writes don't immediately trigger for pure interval policy
        return False

    def should_snapshot_now(self) -> bool:
        with self._lock:
            return (time.monotonic() - self._last_snapshot) >= self.interval

    def mark_snapshot_completed(self) -> None:
        with self._lock:
            self._last_snapshot = time.monotonic()
