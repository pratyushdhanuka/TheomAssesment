import json
import os
import threading
import time
from typing import Any, Optional, List, Dict
from snapshot import ISnapshotStore, ISnapshotPolicy


class KVStore:
    def __init__(self, node_id: str, peer_nodes: List[str], snapshot_store: ISnapshotStore, snapshot_policy: Optional[ISnapshotPolicy] = None):
        self.node_id = node_id
        self.peer_nodes = peer_nodes
        self.all_nodes = sorted([node_id] + peer_nodes)
        self.snapshot_store = snapshot_store
        self.snapshot_policy = snapshot_policy
        self.store = {}
        self.lock = threading.Lock()
        self.log_file = f"{self.node_id}_wal.log"
        self._load_from_disk()
        # start background snapshot worker if a policy was provided
        if self.snapshot_policy is not None:
            self._snapshot_thread = threading.Thread(target=self._snapshot_worker, daemon=True)
            self._snapshot_thread.start()

    def _create_snapshot(self):
        # take a consistent copy under lock
        with self.lock:
            snapshot_data = dict(self.store)

        try:
            self.snapshot_store.save_snapshot(self.node_id, snapshot_data)
            # truncate WAL after successful snapshot to avoid replaying already-snapshotted records
            try:
                with self.lock:
                    # clear the WAL file
                    open(self.log_file, "w").close()
            except Exception:
                # best-effort: ignore failures to truncate
                pass
        except Exception:
            # best-effort: ignore snapshot save failures
            pass
        
    def send_to_node(self, target_node: str, message: dict) -> Optional[dict]:
        pass  # provided

    def _owner_for_key(self, key: str) -> str:
        return self.all_nodes[hash(key) % len(self.all_nodes)]

    def _buddy_for_owner(self, owner: str) -> str:
        idx = self.all_nodes.index(owner)
        return self.all_nodes[(idx + 1) % len(self.all_nodes)]

    def _append_wal(self, record: dict):
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record) + "\n")

    def _load_from_disk(self):
        snap = self.snapshot_store.load_snapshot(self.node_id)
        if snap:
            self.store = snap

        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                for line in f:
                    rec = json.loads(line.strip())
                    self.store[rec["key"]] = rec["value"]
    def on_message(self, from_node: str, message: dict) -> dict:
        action = message.get("action")

        if action == "replica_put":
            key = message["key"]
            value = message["value"]

            with self.lock:
                self.store[key] = value
                self._append_wal({"key": key, "value": value})
            return {"ok": True}

        if action == "forward_put":
            return {"ok": self.put(message["key"], message["value"])}

        if action == "forward_get":
            value = self.get(message["key"])
            return {"ok": True, "value": value}

        return {"ok": False}

    def get(self, key: str) -> Optional[Any]:
        owner = self._owner_for_key(key)

        if owner == self.node_id:
            with self.lock:
                return self.store.get(key)

        resp = self.send_to_node(owner, {"action": "forward_get", "key": key})
        if resp and resp.get("ok"):
            return resp.get("value")

        buddy = self._buddy_for_owner(owner)
        if buddy == self.node_id:
            with self.lock:
                return self.store.get(key)

        resp = self.send_to_node(buddy, {"action": "forward_get", "key": key})
        return resp.get("value") if resp and resp.get("ok") else None

    def put(self, key: str, value: Any) -> bool:
        owner = self._owner_for_key(key)

        if owner != self.node_id:
            resp = self.send_to_node(owner, {
                "action": "forward_put",
                "key": key,
                "value": value
            })
            return bool(resp and resp.get("ok"))

        with self.lock:
            self.store[key] = value
            self._append_wal({"key": key, "value": value})

        buddy = self._buddy_for_owner(owner)
        if buddy != self.node_id:
            self.send_to_node(buddy, {
                "action": "replica_put",
                "key": key,
                "value": value
            })

        # let policy decide if we should snapshot immediately
        try:
            if self.snapshot_policy is not None and self.snapshot_policy.on_write():
                self._create_snapshot()
                try:
                    self.snapshot_policy.mark_snapshot_completed()
                except Exception:
                    pass
        except Exception:
            # ignore policy errors
            pass

        return True

    def _snapshot_worker(self):
        # periodic background worker that asks the policy whether to snapshot
        while True:
            try:
                if self.snapshot_policy is not None and self.snapshot_policy.should_snapshot_now():
                    self._create_snapshot()
                    try:
                        self.snapshot_policy.mark_snapshot_completed()
                    except Exception:
                        pass
            except Exception:
                # ignore policy errors and continue
                pass
            time.sleep(1.0)
