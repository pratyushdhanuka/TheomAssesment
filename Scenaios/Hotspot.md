# Hotspot / Skew Handling – Design Notes

## 🧠 Problem

In a deterministic ownership model:

- owner = hash(key) % 3
- 
Load may become uneven if:
- access pattern is skewed
- few keys receive most traffic
- hot keys dominate reads/writes

---

## ⚠️ Impact

### 1. Write Bottleneck
- single owner handles all writes
- increased latency

### 2. Read Bottleneck
- owner overloaded with reads

### 3. Resource Imbalance
- one node heavily used
- others underutilized

### 4. Stability Risk
- overloaded node may become slow/unhealthy

---

## 🧩 Root Cause

Mismatch between:
- **key distribution** (balanced)
- **access distribution** (skewed)

---

## 🛠️ Countermeasures

### 1. Read from Buddy
- serve reads from replica
- reduces owner load

**Pros**
- simple
- no design change

**Cons**
- stale reads possible

---

### 2. Hot-Key Caching (All Nodes)
- cache frequently accessed keys everywhere

**Pros**
- best read performance
- reduces owner pressure

**Cons**
- cache invalidation complexity
- stale data risk

---

### 3. Virtual Shards
- hash into many buckets → assign to nodes

**Pros**
- better distribution overall

**Cons**
- more routing complexity
- doesn’t fix single hot key

---

### 4. Split Logical Keys (App-level)
- break large hot objects into smaller keys

**Pros**
- distributes load

**Cons**
- requires app changes

---

### 5. Full Replication for Hot Keys
- replicate hot keys to all nodes
- reads served from any node

**Pros**
- highest read scalability

**Cons**
- replication overhead
- stale reads risk

---

## 🎯 Recommended Approach

### Base Design
- single owner + buddy replication

### Optimization Layer
- hot-key caching
- read from buddy

---

## ⚖️ Tradeoffs

| Approach | Benefit | Tradeoff |
|----------|--------|----------|
| Buddy reads | simple scaling | stale reads |
| Hot-key cache | high performance | invalidation complexity |
| Virtual shards | balanced load | complexity |
| Key splitting | scalable writes | app dependency |
| Full replication | max availability | overhead |

---

## 🧠 Final Insight

> Deterministic ownership ensures consistency, but skewed access creates hotspots.  
> Optimization should focus on read distribution without breaking the single-writer model.