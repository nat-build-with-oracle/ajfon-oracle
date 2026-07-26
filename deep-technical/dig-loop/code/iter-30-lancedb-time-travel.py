"""Dig-loop 30/50 — Time-travel: every write is a NEW version, nothing is lost.

Grounded in book/15-lancedb-time-travel.md (LanceDB keeps every version of the
data via Lance's columnar format -- checkout(version) to view history,
restore() to undo a bad delete; real demo: delete n1 by mistake -> checkout
the version before the delete -> restore() -> n1 comes back, and the delete
itself stays visible in history for audit).
Runnable standalone (stdlib only):  python iter-30-lancedb-time-travel.py

Builds a small real MVCC-style versioned table: add/delete never mutate old
snapshots in place -- every write appends a new immutable version. restore()
doesn't rewrite history either; it just appends ANOTHER new version copied
from the old one (like `git revert`, not `git reset --hard`).
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""


class VersionedTable:
    def __init__(self):
        self.versions = [{}]   # version 1: empty table

    @property
    def current_version(self):
        return len(self.versions)

    def _current_rows(self):
        return dict(self.versions[-1])

    def add(self, rows):
        new_state = self._current_rows()
        for row in rows:
            new_state[row["id"]] = row
        self.versions.append(new_state)
        return self.current_version

    def delete(self, row_id):
        new_state = self._current_rows()
        new_state.pop(row_id, None)
        self.versions.append(new_state)
        return self.current_version

    def checkout(self, version):
        """View an OLD version WITHOUT touching current state at all."""
        return dict(self.versions[version - 1])

    def restore(self, version):
        """Undo: append a NEW version that copies the OLD state -- history
        (including the bad delete) is never erased, only added to."""
        restored_state = dict(self.versions[version - 1])
        self.versions.append(restored_state)
        return self.current_version

    def list_versions(self):
        return list(range(1, len(self.versions) + 1))


tbl = VersionedTable()

v1 = tbl.current_version
print(f"=== v{v1}: empty table ===")

v2 = tbl.add([
    {"id": "n1", "text": "ประชุมกับอาจารย์ฝน เรื่อง workshop", "vec": [0.9, 0.1]},
    {"id": "n2", "text": "สูตรกาแฟ cold brew", "vec": [0.1, 0.9]},
    {"id": "n3", "text": "งบประมาณโครงการปีหน้า", "vec": [0.3, 0.3]},
])
print(f"=== v{v2}: add n1, n2, n3 ===")
print(f"current rows: {sorted(tbl._current_rows().keys())}")

v3 = tbl.delete("n1")   # "สมมติลบผิด!" -- book/15's real accidental-delete scenario
print(f"\n=== v{v3}: delete n1 (BY MISTAKE) ===")
print(f"current rows: {sorted(tbl._current_rows().keys())}")

# --- checkout the version BEFORE the mistaken delete ------------------------
pre_delete_state = tbl.checkout(v2)
print(f"\n=== checkout(v{v2}) -- viewing history WITHOUT changing current ===")
print(f"v{v2} rows: {sorted(pre_delete_state.keys())}")
print(f"current (v{tbl.current_version}) rows still: {sorted(tbl._current_rows().keys())}  <- unchanged by checkout")

# --- restore: undo the bad delete --------------------------------------------
v4 = tbl.restore(v2)
print(f"\n=== restore(v{v2}) -> creates v{v4} ===")
print(f"current rows: {sorted(tbl._current_rows().keys())}  <- n1 is BACK")
print(f"all versions ever created: {tbl.list_versions()}  <- v{v3} (the mistake) is still in history for audit")


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb)


def search(state, qvec, k=1):
    scored = [(rid, cosine(qvec, row["vec"])) for rid, row in state.items()]
    return sorted(scored, key=lambda x: -x[1])[:k]


query_vec = [0.85, 0.15]   # meaning-close to n1 ("meeting")
result_at_v3 = search(tbl.checkout(v3), query_vec)     # n1 was deleted here
result_at_v4 = search(tbl.checkout(v4), query_vec)     # n1 is restored here

print(f"\n=== same query, different point in time ===")
print(f"search at v{v3} (n1 deleted)  -> {result_at_v3}")
print(f"search at v{v4} (n1 restored) -> {result_at_v4}")

# --- asserts -----------------------------------------------------------------
# 1. deleting must not destroy old versions -- checkout(v2) must still have n1
assert "n1" in tbl.checkout(v2), "checking out a pre-delete version must still contain the deleted row"

# 2. the CURRENT state right after delete must NOT have n1
current_after_delete = tbl.checkout(v3)
assert "n1" not in current_after_delete, "the version right after delete must genuinely lack the deleted row"

# 3. restore() must bring n1 back into the LATEST (current) state
assert "n1" in tbl._current_rows(), "after restore(), n1 must be back in the current/latest state"

# 4. restore() must be a NEW version (append), not an in-place rewrite --
#    the version count must have grown, and the mistake (v3) must remain
assert tbl.current_version == 4, "restore() must create a new version 4, not rewrite version 3"
assert v3 in tbl.list_versions(), "the mistaken delete version must remain visible in history (audit trail)"

# 5. checkout() must be read-only: viewing history must never mutate the
#    table's actual current/latest version
before_checkout = dict(tbl._current_rows())
_ = tbl.checkout(1)   # look at the very first (empty) version
after_checkout = dict(tbl._current_rows())
assert before_checkout == after_checkout, "checkout() must be strictly read-only and never change current state"

# 6. the same query against different versions must give different results --
#    proving time-travel genuinely reproduces "what search saw back then"
assert result_at_v3[0][0] != "n1", "at v3 (post-delete), n1 must not be the top search result (it's gone)"
assert result_at_v4[0][0] == "n1", "at v4 (post-restore), n1 must be back as the top search result"

print("\n✓ all self-checks passed — every write is a new version; delete doesn't erase history; restore = undo, not rewrite.")
