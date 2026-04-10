from .ISnapshotPolicy import ISnapshotPolicy
from .count_snapshot_policy import CountSnapshotPolicy
from .interval_snapshot_policy import IntervalSnapshotPolicy

class HybridSnapshotPolicy(ISnapshotPolicy):
    def __init__(self, count_threshold: int = 100, interval_seconds: float = 30.0):
        self.count_policy = CountSnapshotPolicy(count_threshold)
        self.interval_policy = IntervalSnapshotPolicy(interval_seconds)

    def on_write(self) -> bool:
        return self.count_policy.on_write()

    def should_snapshot_now(self) -> bool:
        return self.interval_policy.should_snapshot_now() or self.count_policy.should_snapshot_now()

    def mark_snapshot_completed(self) -> None:
        self.count_policy.mark_snapshot_completed()
        self.interval_policy.mark_snapshot_completed()
