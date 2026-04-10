import json
import os
import threading
import time
from typing import Any, Optional, List, Dict
from snapshot import ISnapshotStore, ISnapshotPolicy


class KVStoreV2:
    # simple in-process registry so nodes can communicate in tests
    _registry: Dict[str, "KVStoreV2"] = {}
    def __init__(self, node_id: str, peer_nodes: List[str], snapshot_store: ISnapshotStore, snapshot_policy: Optional[ISnapshotPolicy] = None):
        self.node_id = node_id
        self.peer_nodes = peer_nodes
        self.all_nodes = sorted([node_id] + peer_nodes)
        self.snapshot_store = snapshot_store
        self.snapshot_policy = snapshot_policy
        self.store = {}
        self.lock = threading.Lock()
        # pending writes that this node has accepted on behalf of some owner while that owner was offline
        # map: owner_node_id -> list of {"key":..., "value":...}
        self.pending_writes: Dict[str, List[Dict[str, Any]]] = {}
        # flag indicating whether this node is currently considered online
        self.is_online = True
        # when a node comes online it may need to receive replayed updates from buddies
        # this flag indicates whether this node still expects to be updated by buddies
        self.needs_replay = False
        self.log_file = f"{self.node_id}_wal.log"
        self._load_from_disk()
        # register in-process
        KVStoreV2._registry[self.node_id] = self
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
        # in-process delivery via registry; return None if target unreachable
        target = KVStoreV2._registry.get(target_node)
        if target is None:
            return None
        if not getattr(target, "is_online", True):
            return None
        try:
            return target.on_message(self.node_id, message)
        except Exception:
            return None

    def set_online(self, online: bool):
        """Mark this node online/offline. When becoming online we announce to peers so they can
        sync any pending writes targeted at us."""
        self.is_online = online
        if online:
            # when coming online, expect to be replayed to by buddies until they finish
            self.needs_replay = True
            total_replayed = 0
            # announce to all peers and wait for their replay responses
            for peer in self.peer_nodes:
                # best-effort announce and collect replay count
                try:
                    resp = self.send_to_node(peer, {"action": "announce_online", "node": self.node_id})
                    if resp and isinstance(resp.get("replayed"), int):
                        total_replayed += resp.get("replayed", 0)
                except Exception:
                    pass
            # once we've processed replies from peers consider ourselves up-to-date
            self.needs_replay = False

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

        if action == "replica_pending_put":
            # another node (buddy) is telling us it accepted a write on behalf of owner
            owner = message["owner"]
            key = message["key"]
            value = message["value"]
            with self.lock:
                # store locally as well so reads can find it when owner is down
                self.store[key] = value
                self._append_wal({"key": key, "value": value})
                # record pending write so we can later replay to owner when it comes online
                self.pending_writes.setdefault(owner, []).append({"key": key, "value": value})
            return {"ok": True}

        if action == "announce_online":
            # a node just announced it is online; if we have pending writes for it, start replay
            node = message.get("node")
            # best-effort: stream pending writes to the node and clear when acknowledged
            pending = self.pending_writes.get(node, [])
            if not pending:
                return {"ok": True, "replayed": 0}

            replayed = 0
            for rec in list(pending):
                resp = self.send_to_node(node, {"action": "replay_put", "key": rec["key"], "value": rec["value"]})
                if resp and resp.get("ok"):
                    replayed += 1
                    pending.remove(rec)
            if not pending:
                self.pending_writes.pop(node, None)
            return {"ok": True, "replayed": replayed}

        if action == "replay_put":
            # owner is receiving replayed writes from buddy
            key = message["key"]
            value = message["value"]
            with self.lock:
                self.store[key] = value
                self._append_wal({"key": key, "value": value})
            # ack
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
                value = self.store.get(key)

            if value is not None:
                return value

            if self.needs_replay == False:
                buddy = self._buddy_for_owner(owner)
                if buddy != self.node_id:
                    resp = self.send_to_node(buddy, {"action": "forward_get", "key": key})
                    if resp and resp.get("ok"):
                        return resp.get("value")

            return None

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
            # try owner first
            resp = self.send_to_node(owner, {
                "action": "forward_put",
                "key": key,
                "value": value
            })
            if resp and resp.get("ok"):
                return True

            # owner unreachable: have buddy accept and record pending write to later replay
            buddy = self._buddy_for_owner(owner)
            if buddy == self.node_id:
                # we are the buddy -> accept write locally and mark pending for owner
                with self.lock:
                    self.store[key] = value
                    self._append_wal({"key": key, "value": value})
                    self.pending_writes.setdefault(owner, []).append({"key": key, "value": value})
                return True

            # send to buddy to accept as pending replica_put
            resp = self.send_to_node(buddy, {
                "action": "replica_pending_put",
                "owner": owner,
                "key": key,
                "value": value,
            })
            return bool(resp and resp.get("ok"))

        # if we are the owner
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
