# Node Health Detection & Impact Notes

## 🎯 Goal

Detect when nodes are **unhealthy/unreachable** and ensure:
- system continues operating
- temporary inconsistency is acceptable

---

## 🧠 Detection Strategy

### Opportunistic Detection

- Based on `send_to_node()` failure:
  - timeout
  - no response
  - error

👉 If communication fails → mark node as **unhealthy (temporarily)**

---

## ⚠️ Important Principle

- Detection is **not perfect**
- System may:
  - falsely mark slow node as down
  - miss short outages

👉 This is acceptable for this design

---

## 🧩 Key Scenarios

### 1. Owner Unreachable
- Writes:
  - forwarded request fails
  - trigger **buddy takeover (if enabled)**
- Reads:
  - fallback to buddy

---

### 2. Buddy Unreachable
- Writes:
  - succeed on owner
  - replication skipped / retried later
- Reads:
  - rely only on owner

---

### 3. Both Nodes Temporarily Unreachable
- Reads may fail
- Writes may fail

👉 System temporarily unavailable

---

### 4. Slow Node (False Negative)
- Node is alive but slow
- System may:
  - mark it unhealthy
  - route traffic elsewhere

👉 Leads to temporary inconsistency

---

### 5. Node Comes Back

- System resumes communication
- No explicit health sync required initially
- Recovery handled via:
  - WAL replay
  - replication sync

---

## 📉 Impact on System Behavior

- Reads may return **stale data**
- Writes may:
  - be delayed
  - be temporarily rerouted
- System prioritizes:
  - **availability over freshness**

---

## ⚖️ Tradeoffs

| Aspect | Impact |
|--------|--------|
| Accuracy | Low (best-effort detection) |
| Availability | High |
| Consistency | Eventual |
| Complexity | Low |

---

## 🧠 Design Positioning

- No dedicated health-check service
- No consensus on node status
- Purely **best-effort failure detection**

---

## 💬 One-line Summary

> “Node health is detected opportunistically through communication failures, accepting temporary misclassification and stale reads in exchange for simplicity and continued availability.”