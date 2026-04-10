# Distributed KV Store – Design Brainstorm Notes

## 🧠 Problem Understanding
We need to design a distributed key-value store across 3 nodes that supports:
- Basic read/write operations
- Data replication
- Fault tolerance (node failure, network issues)
- Persistence across restarts
- Periodic backups without losing writes

---

## ⚙️ Core Assumptions

- Fixed **3-node cluster**
- Moderate data size (fits in memory + disk per node)
- Single node failure at a time
- Clients can hit **any node**
- Network is unreliable but not fully partitioned
- Keys are either client-provided or globally unique
- Focus is on **clarity over extreme scale**

---

## 🧩 Key Design Decisions

### 1. Single Owner per Key

**Design**
- owner = hash(key) % 3
- Each key has exactly **one authoritative node**
- All writes must go through this owner

**Pros**
- Eliminates write conflicts
- No need for distributed consensus
- Simple reasoning

**Cons**
- Owner becomes write bottleneck for that key
- Requires routing/forwarding

**Tradeoff**
- Choosing **simplicity + consistency** over multi-writer complexity

---

### 2. Buddy Replication

**Design**
- buddy = next node in ring

- Each key is stored on:
  - 1 owner
  - 1 replica (buddy)

**Pros**
- Protects against single node failure
- Simple deterministic mapping
- No coordination required

**Cons**
- Only 2 copies → some edge cases of dual failure unsafe
- Replica can be slightly stale

**Tradeoff**
- Chose **minimal replication (2 copies)** for simplicity

---

### 3. Write Flow

**Flow**
1. Any node receives request
2. Computes owner
3. Forwards to owner (if needed)
4. Owner:
   - writes to memory
   - appends to WAL
   - replicates to buddy

**Pros**
- Single source of truth
- Ordered writes
- Easy to reason about

**Cons**
- Extra network hop if request not on owner
- Replication can fail temporarily

**Tradeoff**
- Accept **extra latency** for clean correctness

---

### 4. Read Flow

**Flow**
- Try owner first
- Fallback to buddy if owner unavailable

**Pros**
- High availability for reads
- Simple fallback logic

**Cons**
- Replica might be slightly stale

**Tradeoff**
- Accept **eventual consistency for reads**

---

## 💾 Persistence Strategy

### Write Ahead Log (WAL)

**Design**
- Every write is appended to disk log

**Pros**
- No data loss on crash
- Simple implementation
- Sequential disk writes (fast)

**Cons**
- Log grows indefinitely
- Recovery time increases over time

---

### Recovery

**Flow**
1. Load snapshot (if exists)
2. Replay WAL

**Pros**
- Accurate reconstruction of state
- No lost writes

---

## 💿 Backup Strategy

### Snapshot + WAL

**Design**
- Periodically snapshot in-memory store
- Continue writing to WAL during snapshot

**Backup =**
- snapshot file
- WAL tail after snapshot point

**Pros**
- No write blocking
- Consistent recovery point
- Efficient restore

**Cons**
- Snapshot may not include latest writes
- Requires WAL replay

**Tradeoff**
- Chose **eventual snapshot consistency + WAL correctness**

---

## ⚠️ Failure Handling

### Node Down Detection
- Based on `send_to_node()` failure / timeout

---

### Owner Failure
- Reads fallback to buddy
- Writes fail or retry

---

### Buddy Failure
- Owner still accepts writes
- Replication can be retried later

---

### Node Restart
- Recover using snapshot + WAL

---

## 🚫 What We Avoided (Intentionally)

- No leader election / consensus (e.g. Raft)
- No multi-writer conflict resolution
- No distributed locking
- No complex sharding rebalancing

**Reason**
- Overkill for 3-node system
- Adds unnecessary complexity for this assignment

---

## 🎯 Design Tradeoffs Summary

| Aspect        | Choice                     | Tradeoff |
|--------------|--------------------------|----------|
| Consistency  | Single owner             | Less parallelism |
| Availability | Read fallback to buddy   | Possible stale reads |
| Durability   | WAL                      | Log growth |
| Backup       | Snapshot + WAL           | Slight recovery complexity |
| Replication  | Owner + 1 replica        | Limited redundancy |

---

## 🧠 Final Mental Model

**Deterministic routing + single writer + buddy replication + WAL + snapshot**

=  
✔ Simple  
✔ Reliable  
✔ Interview-friendly  
✔ Covers all requirements cleanly  

---

## 💬 One-line Summary

> “I use deterministic key ownership to ensure single-writer consistency, replicate to a buddy node for fault tolerance, persist via WAL for durability, and combine periodic snapshots with WAL replay for consistent backups without blocking writes.”