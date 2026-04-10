# Snapshot Policy Notes

## Goal
Introduce a clean `ISnapshotPolicy` abstraction so snapshot timing logic stays separate from snapshot persistence logic.

---

## Core Design Split

### `ISnapshotStore`
Responsible only for snapshot persistence:
- save snapshot
- load snapshot
- optionally delete / replace snapshot

It should **not** decide:
- when to snapshot
- whether snapshot is interval-based
- whether snapshot is count-based

---

### `ISnapshotPolicy`
Responsible for deciding **when** to create a snapshot.

This allows different strategies:
- count-based
- interval-based
- hybrid

---

## Why This Separation Is Good

### Clear responsibility
- `ISnapshotStore` = **where/how snapshot is stored**
- `ISnapshotPolicy` = **when snapshot should happen**

### Easier to extend
Later we can plug in:
- `CountSnapshotPolicy`
- `IntervalSnapshotPolicy`
- `HybridSnapshotPolicy`

without changing `KVStore` much.

### Easier to test
We can test:
- policy logic independently
- snapshot store independently
- KVStore orchestration independently

---

## Recommended `ISnapshotPolicy` Behavior

A snapshot policy should support two trigger styles:

### 1. Count-based trigger
Useful when write volume is high.

Example:
- snapshot every 100 writes

Good for:
- keeping WAL from growing too large
- high-throughput systems
- reducing recovery replay time

---

### 2. Interval-based trigger
Useful when writes are low or unpredictable.

Example:
- snapshot every 30 seconds

Good for:
- ensuring snapshots still happen during low traffic
- bounding recovery staleness
- simpler operational tuning

---

### 3. Hybrid trigger
Best production option.

Snapshot when:
- write count threshold reached, **or**
- time interval exceeded

Good for:
- bursty workloads
- predictable recovery
- WAL growth control

---

## Suggested Interface Idea

```python
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