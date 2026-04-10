# Distributed KV Store – Tradeoffs & Failure Scenarios

## ⚠️ First Principle

There is **no perfect solution** in distributed systems.  
Every design choice comes with tradeoffs between:

- Consistency vs Availability  
- Simplicity vs Robustness  
- Latency vs Durability  
- Implementation effort vs correctness  

This design intentionally prioritizes:
- simplicity
- determinism
- clarity of behavior

over advanced fault-handling mechanisms.

---

## 🐢 What Happens If a Node Is Slow?

### Scenario
- Owner node is slow
- Buddy node is slow

### Impact

**Slow Owner**
- Write latency increases (all writes routed through owner)
- Read latency increases (primary reads go to owner)

**Slow Buddy**
- Replication becomes delayed
- Data still safe on owner, but replica is stale

### Handling

- Reads fallback to buddy if owner times out
- Writes still go through owner (cannot bypass safely)
- Replication can be async (best-effort)

### Tradeoff

- Strong consistency (single owner)
- but **write performance depends on owner health**

---

## 🔴 What Happens If a Node Is Down?

### Scenario 1: Owner Down

**Impact**
- Writes for that key cannot be completed
- Reads fallback to buddy

**Handling**
- Retry writes
- Or fail fast (depending on system requirement)

**Tradeoff**
- Design sacrifices write availability for consistency

---

### Scenario 2: Buddy Down

**Impact**
- Writes succeed on owner
- No replication → temporary loss of redundancy

**Handling**
- Continue writes
- Track replication failures (future improvement)

**Tradeoff**
- System remains available
- but temporarily less fault tolerant

---

## 🔁 What Happens When a Node Comes Back Up?

### Scenario
- Node restarts after crash

### Recovery

- Load snapshot (if available)
- Replay WAL to rebuild state

### Limitation

- Node may miss updates that happened while it was down

### Possible Improvement (not implemented)

- Sync with owner/buddy
- Fetch missed updates

### Tradeoff

- Simple recovery logic
- but no automatic repair of stale replicas

---

## ⚔️ What If Two Users Write the Same Key at the Same Time?

### Problem

- Two writes arrive at different nodes
- Network delay causes reordering

### Risk

- Conflicting updates
- inconsistent state across nodes

---

### Solution

- Route all writes to **single owner**
- Owner processes writes sequentially

### Result

- Writes are serialized
- Owner defines final order

---

### Limitation

- Order is based on arrival at owner, not real-world timing
- No merge/conflict resolution

### Tradeoff

- Simplicity and determinism
- over correctness of "true" concurrent intent

---

## 💾 How Does Backup Interact with Ongoing Writes?

### Problem

- Backup may miss writes happening during snapshot
- Blocking writes is unacceptable

---

### Solution: Snapshot + WAL

**During backup:**
- Take snapshot of current in-memory store
- Continue writing to WAL

**During recovery:**
- Load snapshot
- Replay WAL entries after snapshot point

---

### Why This Works

- Snapshot provides consistent base
- WAL captures all new writes
- No writes are lost

---

### Limitation

- Snapshot is not perfectly up-to-date
- Requires WAL replay for full consistency

### Tradeoff

- No write blocking
- Slightly more complex recovery

---

## ⚠️ Other Edge Cases & Limitations

### Infinite Replication Loops
- Prevented by separating:
  - `forward_put` (client → owner)
  - `replica_put` (owner → replica)

---

### Partial Failures
- Network partition between nodes
- Some nodes may have stale data

**Not fully solved in this design**

---

### No Consensus Mechanism
- No Raft/Paxos
- No quorum writes

**Implication**
- Simpler system
- but weaker guarantees in extreme failure cases

---

## 🎯 Final Tradeoff Summary

| Concern | Chosen Approach | Tradeoff |
|--------|----------------|----------|
| Write Conflicts | Single owner | Lower write availability |
| Replication | Buddy only | Limited redundancy |
| Durability | WAL | Log growth |
| Backup | Snapshot + WAL | Recovery complexity |
| Failure Detection | RPC failure | Reactive only |
| Recovery | Local replay | No automatic resync |

---

## 🧠 Final Thought

This system is:

- **not perfect**
- **not fully fault-tolerant under all conditions**
- **not strongly consistent under partitions**

But it is:

- simple
- deterministic
- correct under normal assumptions
- and sufficient for the scope of the assignment

---

## 💬 One-Line Reflection

> "I intentionally chose a simple single-owner + replica design that avoids distributed coordination complexity, while still handling the most common failure scenarios with clear and predictable behavior."