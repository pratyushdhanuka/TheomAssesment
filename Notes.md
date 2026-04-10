🧠 Problem Framing
# Notes

🧠 Problem Framing

Build a distributed KV store (3 nodes)

Ensure:
- consistency (no conflicting writes)
- fault tolerance (1 node failure)
- durability (restart safe)
- live backups (no write loss)

⚙️ Core Design Decisions

1. Data Ownership
   - `owner = hash(key) % 3`
   - Only owner node writes
   - Others forward requests

   👉 avoids concurrent write conflicts

2. Replication Strategy
   - Each key has 1 buddy replica
   - `buddy = next node in ring`

   👉 ensures 2 copies of data

3. Write Flow
   - Any node receives request
   - Routes to owner
   - Owner:
     - writes to memory
     - appends to WAL
     - replicates to buddy

   👉 single source of truth

4. Read Flow
   - Read from owner
   - If owner down → read from buddy

   👉 maintains availability

💾 Persistence Strategy

WAL (Write Ahead Log)
- Every write appended to disk
- Guarantees no data loss on crash

Recovery
- On restart:
  - load snapshot (if exists)
  - replay WAL

💿 Backup Strategy

Snapshot + WAL
- Periodically snapshot memory → file
- Continue writing to WAL during backup

Recovery:
- load snapshot
- replay WAL after snapshot

👉 solves consistent backup with live writes

⚠️ Failure Handling

- Owner down: reads from buddy
- Buddy down: write succeeds (replication retry later)
- Node restart: recover via WAL + snapshot
- Network issues: detected via `failed send_to_node`

🎯 Tradeoffs & Reasoning

- Consistency > Availability (writes)
- No multi-writer → simpler system
- No consensus → faster, easier
- Accept eventual replica sync

🧾 Final Mental Model

👉 Deterministic routing + single writer + replica + WAL + snapshot

---

Simple, reliable, and interview-friendly distributed KV store 🚀
