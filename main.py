from KVStore import KVStore
from snapshot.in_memory_snapshot_store import InMemorySnapshotStore


def main():
    snap = InMemorySnapshotStore()
    store = KVStore("node1", ["node2", "node3"], snapshot_store=snap)
    store.put("user:1", {"name": "Alice", "email": "alice@example.com"})
    print(store.get("user:1"))


if __name__ == "__main__":
    main()
