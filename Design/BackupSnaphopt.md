# Backup Strategy – Design Notes

## 🧠 Goal
Design a backup mechanism that:
- Ensures **consistency**
- Works while **writes continue**
- Supports **reliable recovery**
- Balances **cost, size, and complexity**

---

## 📌 Key Assumptions

- System has **3 nodes**
- Each node maintains:
  - in-memory store
  - WAL for durability
- Backup is required for:
  - node crash recovery
  - disaster recovery (optional)
- Data size is **moderate but may grow**
- Consistency is the **primary requirement**

---

## ⚠️ First Principle

There is **no perfect backup solution**.

Every approach trades off between:
- cost
- storage size
- recovery speed
- implementation complexity
- durability

---

## 🎯 Core Requirement

Backup must:
- not block writes
- not lose writes during backup
- allow deterministic restore

---

## 🧩 Chosen Approach (Base)

### Snapshot + WAL

- Take periodic **snapshot of in-memory store**
- Continue writing to **WAL during snapshot**
- Restore using:
  - snapshot
  - WAL replay after snapshot

### Why

- Snapshot alone is insufficient
- WAL ensures **no write loss**
- Together → consistent recovery

---

## 🔍 Key Design Considerations

### 1. Consistency
- Snapshot must represent a **valid state**
- WAL bridges gap between snapshot and current state

---

### 2. Performance Impact
- Avoid blocking writes
- Snapshot should be lightweight (copy + async persist)

---

### 3. Recovery Speed
- Snapshot reduces replay time
- WAL-only recovery is slow

---

### 4. Storage Size
- Full snapshot → large but simple
- Incremental backup → efficient but complex

---

### 5. Durability
- Local backup is not enough for full failure
- Remote storage improves safety

---

### 6. Atomicity
- Snapshot must be saved atomically
- Partial snapshot = corrupt restore

---

## 🧠 Backup Options (Based on Cost & Scale)

---

### Option 1: Local Full Snapshot

**Design**
- Store snapshot on local disk
- WAL stored locally

**Pros**
- Very simple
- Low cost
- Fast recovery

**Cons**
- No protection against machine failure
- Snapshot size grows with data

**Best for**
- small systems
- low-cost environments

---

### Option 2: Local Snapshot + WAL + S3 Backup

**Design**
- Snapshot stored locally
- WAL stored locally
- Periodically upload snapshot/WAL to S3

**Pros**
- Fast local recovery
- Remote disaster recovery
- Balanced cost

**Cons**
- Slight complexity in syncing
- Storage cost in S3

**Best for**
- production-like systems
- moderate data size

---

### Option 3: Incremental / Chunked Backup to S3

**Design**
- Base snapshot stored in S3
- Upload only incremental changes (WAL segments or chunks)

**Pros**
- Efficient storage usage
- Scales for large datasets
- Reduced network cost

**Cons**
- Complex implementation
- Harder recovery logic

**Best for**
- large-scale systems
- cost-sensitive storage environments

---

## ⚖️ Tradeoff Summary

| Aspect | Option 1 | Option 2 | Option 3 |
|------|--------|--------|--------|
| Cost | Low | Medium | Optimized long-term |
| Complexity | Very low | Medium | High |
| Recovery Speed | Fast | Fast | Medium |
| Durability | Weak | Strong | Strong |
| Scalability | Low | Medium | High |

---

## 🧾 Final Recommendation

For this assignment:

> Use **local snapshot + WAL** as base  
> and optionally extend to **S3 backup for durability**

This provides:
- consistency
- simple restore flow
- scalability path
- clear tradeoff awareness

---

## 💬 One-line Summary

> “I use snapshot + WAL to ensure consistent backups without blocking writes, and scale the backup strategy from local storage to S3-based incremental backups depending on cost and data size constraints.”