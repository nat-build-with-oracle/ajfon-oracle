"""Dig-loop 49/50 — Monitoring: cached stats can lie, live health can't.

Grounded in deep-technical/23-deployment-monitoring.md §23.3 (real incident,
#2759: /api/stats read a CACHED snapshot from boot time and said "ok", while
/api/health did a LIVE probe and correctly said "down" -- TWO endpoints
disagreeing at the same instant, because one was stale and one was live --
"silent degradation": a stale value can lie that a system is healthy while
it's actually broken) and §23.6 (canary recall monitoring: periodically
rerun a golden-set subset to catch quality regressions automatically).
Runnable standalone (stdlib only):  python iter-49-monitoring-drift.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""


class Embedder:
    """A toy embedder that can silently go down after boot."""
    def __init__(self):
        self.alive = True

    def embed(self, text):
        if not self.alive:
            raise TimeoutError("embedder unreachable")
        return [0.1, 0.2, 0.3]

    def kill(self):
        self.alive = False


class OracleServer:
    def __init__(self, embedder):
        self.embedder = embedder
        # §23.3's real bug: this snapshot is taken ONCE at boot and never
        # refreshed -- exactly what /api/stats did
        self._cached_status_at_boot = self._probe_embedder()

    def _probe_embedder(self):
        try:
            self.embedder.embed("healthcheck")
            return "ok"
        except TimeoutError:
            return "down"

    def get_stats(self):
        """THE BUG: reads the cached boot-time snapshot -- never re-probes."""
        return {"vector_status": self._cached_status_at_boot}

    def get_health(self):
        """THE FIX: probes the embedder LIVE, right now, every call."""
        return {"embedderStatus": self._probe_embedder()}

    def get_stats_fixed(self):
        """post-#2759 fix: stats ALSO does a live probe -- no more staleness."""
        return {"vector_status": self._probe_embedder()}


embedder = Embedder()
server = OracleServer(embedder)

print("=== boot: embedder healthy ===")
print(f"stats:  {server.get_stats()}")
print(f"health: {server.get_health()}")

# --- the embedder dies AFTER boot, with no server restart ------------------
embedder.kill()

print("\n=== embedder dies silently after boot (no restart) ===")
stats_after = server.get_stats()
health_after = server.get_health()
print(f"stats:  {stats_after}   <- STALE, still says ok!")
print(f"health: {health_after}   <- LIVE, correctly says down")
print(f"\n2 endpoints disagree at the SAME instant -- this is the real §23.3 incident")

fixed_stats_after = server.get_stats_fixed()
print(f"\n=== after the #2759 fix: stats ALSO probes live ===")
print(f"stats (fixed): {fixed_stats_after}   <- now agrees with health")


# --- canary recall monitoring (§23.6): rerun a golden-set subset ------------
GOLDEN_CANARY = {
    "q1": {"correct_answer": "d1"},
    "q2": {"correct_answer": "d2"},
    "q3": {"correct_answer": "d3"},
}


def search_engine(query_id, embedder_alive):
    """Simulates search quality: when the embedder is down, search
    degrades and returns nothing useful (matches §23.4's real failure mode
    before #2747's fallback was deployed)."""
    if not embedder_alive:
        return None
    return GOLDEN_CANARY[query_id]["correct_answer"]


def run_canary(embedder_alive):
    hits = sum(1 for q in GOLDEN_CANARY if search_engine(q, embedder_alive) == GOLDEN_CANARY[q]["correct_answer"])
    return hits / len(GOLDEN_CANARY)


canary_before = run_canary(embedder_alive=True)
canary_after = run_canary(embedder_alive=False)

print(f"\n=== §23.6: canary recall monitoring ===")
print(f"canary recall while embedder alive = {canary_before:.2f}")
print(f"canary recall after embedder dies  = {canary_after:.2f}  <- automated alarm should fire")

# --- asserts -----------------------------------------------------------------
# 1. after the embedder dies WITHOUT a restart, stats must remain STALE
#    ("ok") -- reproducing the real #2759 bug exactly
assert stats_after == {"vector_status": "ok"}, \
    "cached stats must remain stale ('ok') after the embedder dies, matching the real #2759 bug"

# 2. health must correctly detect the failure LIVE -- the two endpoints
#    must genuinely DISAGREE at the same instant
assert health_after == {"embedderStatus": "down"}, \
    "live health probe must correctly detect the embedder is down"
assert stats_after["vector_status"] != health_after["embedderStatus"], \
    "stats and health must disagree after a silent post-boot failure -- this IS the incident"

# 3. the fixed stats endpoint must now AGREE with health -- proving the
#    #2759 fix (live-probe stats) actually resolves the disagreement
assert fixed_stats_after == {"vector_status": "down"}, \
    "the fixed stats endpoint must report 'down' once it also probes live"

# 4. canary recall must correctly detect the quality regression -- dropping
#    to 0 when the embedder is down, providing an automated signal
assert canary_before == 1.0, "canary recall must be perfect while the embedder is healthy"
assert canary_after == 0.0, "canary recall must crash to 0 when the embedder silently dies"

print("\n✓ all self-checks passed — cached status can lie about a live failure; only a live probe (or canary recall) catches it.")
