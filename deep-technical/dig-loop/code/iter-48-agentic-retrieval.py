"""Dig-loop 48/50 — Agentic retrieval: loop-until-dry beats single-shot.

Grounded in deep-technical/35-agentic-retrieval-loop.md §35.0 (single-shot
retrieve is not enough for complex/long-tail questions) and §35.4 (iterative
refinement, the actual /ralph-dig pattern: keep searching, refining the
query from each round's fresh gap, until K consecutive rounds turn up
NOTHING new -- not a fixed round count, which would risk stopping too early
or wasting rounds too late).
Runnable standalone (stdlib only):  python iter-48-agentic-retrieval.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""

# --- a corpus where different clusters only surface under DIFFERENT query
#     terms -- a single query can only ever find its own cluster ------------
SEARCH_INDEX = {
    "เบาหวาน AI": {"d1", "d2"},                       # round 0: the original query
    "machine learning วินิจฉัย": {"d2", "d3"},           # round 1: refined from d2's topic
    "HbA1c biomarker": {"d3", "d4"},                    # round 2: refined from d3's topic
    "retinal imaging screening": {"d4"},                # round 3: refined from d4's topic -- no NEW docs beyond here
}
ALL_RELEVANT_DOCS = {"d1", "d2", "d3", "d4"}


def search(query):
    return SEARCH_INDEX.get(query, set())


def refine(query, fresh_docs):
    """Pick the next query based on what fresh docs were just found --
    a simplified stand-in for an agent reading the new docs and deciding
    what to search next (§35.4's actual refine() step)."""
    order = list(SEARCH_INDEX.keys())
    idx = order.index(query)
    return order[idx + 1] if idx + 1 < len(order) else query   # stay put if no more queries defined


# --- single-shot baseline ---------------------------------------------------
single_shot_results = search("เบาหวาน AI")
single_shot_recall = len(single_shot_results & ALL_RELEVANT_DOCS) / len(ALL_RELEVANT_DOCS)

print("=== single-shot retrieval ===")
print(f"query 'เบาหวาน AI' -> {single_shot_results}")
print(f"recall = {single_shot_recall:.2f}  (misses the long tail entirely)")


# --- loop-until-dry (§35.4's exact pseudocode) ------------------------------
def loop_until_dry(start_query, dry_limit=2, max_rounds=20):
    seen = set()
    query = start_query
    dry_count = 0
    rounds = []
    for _ in range(max_rounds):
        results = search(query)
        fresh = results - seen
        rounds.append({"query": query, "results": results, "fresh": fresh})
        if not fresh:
            dry_count += 1
        else:
            dry_count = 0
            seen |= fresh
            query = refine(query, fresh)
        if dry_count >= dry_limit:
            break
    return seen, rounds, dry_count


agentic_seen, rounds_log, final_dry_count = loop_until_dry("เบาหวาน AI", dry_limit=2)
agentic_recall = len(agentic_seen & ALL_RELEVANT_DOCS) / len(ALL_RELEVANT_DOCS)

print(f"\n=== §35.4 loop-until-dry (stop after 2 consecutive dry rounds) ===")
for i, r in enumerate(rounds_log):
    print(f"  round {i}: query='{r['query']}' -> fresh={r['fresh'] or '{}'}")
print(f"total found = {agentic_seen}")
print(f"recall = {agentic_recall:.2f}  (found the whole long tail)")
print(f"stopped after {len(rounds_log)} rounds, final dry_count={final_dry_count}")

# --- what a NAIVE fixed-round-count agent (always exactly 2 rounds,
#     regardless of dryness) would have missed --------------------------
naive_fixed_seen, _, _ = loop_until_dry("เบาหวาน AI", dry_limit=999, max_rounds=2)
naive_fixed_recall = len(naive_fixed_seen & ALL_RELEVANT_DOCS) / len(ALL_RELEVANT_DOCS)
print(f"\nnaive fixed-2-rounds agent recall = {naive_fixed_recall:.2f}  <- stops too early, misses tail")

# --- asserts -----------------------------------------------------------------
# 1. single-shot must genuinely miss most of the corpus -- proving why
#    agentic retrieval is needed at all
assert single_shot_recall < 0.6, "single-shot retrieval must miss most of the long-tail relevant docs"

# 2. loop-until-dry must achieve FULL recall -- it keeps going until truly
#    nothing new turns up, so nothing gets left behind
assert agentic_recall == 1.0, "loop-until-dry must eventually find ALL relevant docs"

# 3. the loop must actually terminate via the dry condition (2 consecutive
#    empty rounds), not just run forever or hit max_rounds
assert final_dry_count == 2, "the loop must stop specifically because it hit the dry_limit, not some other reason"

# 4. the loop must NOT run needlessly long -- it should stop shortly after
#    the corpus is exhausted, not churn through all max_rounds
assert len(rounds_log) < 20, "loop-until-dry must terminate well before the max_rounds safety cap"

# 5. a naive FIXED round count (not dry-based) must underperform the
#    dry-based stopping condition -- proving WHY "until dry" beats "N rounds"
assert naive_fixed_recall < agentic_recall, \
    "a naive fixed-round-count agent must recall less than the loop-until-dry agent"

# 6. every round's fresh docs must be genuinely NEW (never re-counted) --
#    sanity check on the seen-set bookkeeping
seen_running = set()
for r in rounds_log:
    assert r["fresh"] == (r["results"] - seen_running), "fresh docs must be exactly results minus everything seen so far"
    seen_running |= r["fresh"]

print("\n✓ all self-checks passed — loop-until-dry finds the full long tail; a fixed round count would have stopped too early.")
