from Snapshot import InMemorySnapshotStore, CountSnapshotPolicy
from KVStore import KVStore


def main():
    snap = InMemorySnapshotStore()
    policy = CountSnapshotPolicy(threshold=100)
    store = KVStore("node1", ["node2", "node3"], snapshot_store=snap, snapshot_policy=policy)
    store.put("user:1", {"name": "Alice", "email": "alice@example.com"})
    print(store.get("user:1"))


if __name__ == "__main__":
    main()
