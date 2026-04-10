# Write Availability – Buddy Takeover Design

## 🧠 Problem

In a strict single-owner model:
- if owner node is down → writes fail

But system has:
- 3 nodes
- at least 2 available nodes

Goal:
👉 **allow writes to continue even if owner is down**

---

## ⚙️ Design Change

### Buddy Takeover

- Each key has:
  - **owner**
  - **buddy (replica)**

### Normal Flow
- Owner handles all writes
- Buddy only replicates

---

### Failure Scenario: Owner Down

When owner is unreachable:

- Buddy becomes **temporary owner**
- Buddy:
  - accepts writes
  - writes to memory
  - writes to WAL
  - marks entries as **pending sync**

---

## 🔄 Recovery Flow (Owner Comes Back)

When owner becomes available again:

- Buddy sends **missed updates** to owner
- Owner applies updates
- Ownership returns to original owner

---

## 📌 Sync Strategy

Sync should be triggered by:
- node recovery detection
- heartbeat / retry mechanism
- first communication attempt

❗ Not only reads — reads alone are insufficient for consistency

---

## 🎯 Benefits

- Writes remain available during owner failure
- System continues operating with 2 nodes
- No need for full leader election

---

## ⚠️ Tradeoffs

### 1. Consistency Risk
- Owner may come back with stale state
- Requires reconciliation

---

### 2. Ordering Complexity
- Writes accepted by buddy may be out of sync with owner’s previous state

---

### 3. Split-Brain Risk (Controlled)
- If multiple nodes think owner is down → conflict risk
- Mitigated by:
  - only allowing **buddy** to take over
  - deterministic mapping

---

### 4. Recovery Complexity
- Need mechanism to:
  - track pending writes
  - replay them to owner
  - ensure idempotency

---

## ⚖️ Tradeoff Summary

| Aspect | Impact |
|--------|--------|
| Availability | Improved (writes continue) |
| Consistency | Slightly weaker during failure |
| Complexity | Increased |
| Recovery | Requires sync logic |

---

## 🧠 Design Positioning

This approach moves system from:
- **strict consistency-first**

to:
- **availability-first with controlled inconsistency**

---

## 💬 One-line Summary

> “To improve write availability, I allow the buddy node to temporarily take over as owner during failures, accept writes with WAL, and reconcile state back to the original owner upon recovery.”