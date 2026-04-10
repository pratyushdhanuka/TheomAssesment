from abc import ABC, abstractmethod

class ISnapshotPolicy(ABC):
    @abstractmethod
    def on_write(self) -> bool:
        """
        Called after a write succeeds.
        Returns True if a snapshot should be created immediately.
        """
        pass

    @abstractmethod
    def should_snapshot_now(self) -> bool:
        """
        Used by periodic/background checks.
        Returns True if a snapshot should be created now.
        """
        pass

    @abstractmethod
    def mark_snapshot_completed(self) -> None:
        """
        Called after snapshot is successfully created.
        Lets policy reset counters/timestamps.
        """
        pass
