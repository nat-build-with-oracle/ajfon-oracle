"""Dig-loop 22/50 — Golden set: the exam you write once, reuse forever.

Grounded in book/11-golden-set-eval.md §11.2/11.5: a golden set is a small,
HUMAN-JUDGED (query, correct_doc_ids) list, built once and re-run after every
change (embedder swap, chunk strategy, threshold tweak). Score drops ->
regression caught immediately. Failed real-world queries get folded back into
the set, so it only ever grows more comprehensive over time.
Runnable standalone (stdlib only):  python iter-22-golden-set.py

This demo focuses on the PROCESS (build once, regression-test, grow the set)
rather than the metric math itself (recall@k = iter-20, MRR/nDCG = iter-21).
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""

# --- v1 golden set: built once, by a human, on day 1 ------------------------
golden_v1 = {
    "อยากสอนเรื่อง AI ค้นหาข้อมูล": {"teaching_note", "ai_search_note"},
    "นัดหมายกับใครไว้บ้าง": {"meeting_note"},
    "สูตรกาแฟ": {"coffee_note"},
}


def make_search_engine(quality):
    """A toy engine: `quality` is a dict mapping query -> set of docs it
    ACTUALLY returns in its top-3 (stands in for a real embedder's behavior)."""
    def search(query):
        return quality.get(query, set())
    return search


def evaluate(golden, search_fn):
    """Regression-test harness: recall@3 over the WHOLE current golden set,
    every time -- exactly what book/11 §11.5 means by 'run evaluate() again'."""
    total_hits, total_relevant = 0, 0
    per_query = {}
    for q, relevant in golden.items():
        found = search_fn(q)
        hits = len(relevant & found)
        per_query[q] = hits == len(relevant)
        total_hits += hits
        total_relevant += len(relevant)
    return total_hits / total_relevant, per_query


# --- day 1: a good model, baseline score recorded ---------------------------
good_model_v1 = make_search_engine({
    "อยากสอนเรื่อง AI ค้นหาข้อมูล": {"teaching_note", "ai_search_note"},
    "นัดหมายกับใครไว้บ้าง": {"meeting_note"},
    "สูตรกาแฟ": {"coffee_note"},
})
baseline_score, baseline_detail = evaluate(golden_v1, good_model_v1)
print(f"=== day 1: baseline recorded on golden_v1 ({len(golden_v1)} queries) ===")
print(f"baseline recall@3 = {baseline_score:.3f}  ({sum(baseline_detail.values())}/{len(golden_v1)} fully correct)")

# --- day 30: someone swaps the embedder (a REGRESSION, unintentional) ------
regressed_model = make_search_engine({
    "อยากสอนเรื่อง AI ค้นหาข้อมูล": {"meeting_note"},   # wrong doc now
    "นัดหมายกับใครไว้บ้าง": {"meeting_note"},            # still fine
    "สูตรกาแฟ": set(),                                    # nothing found
})
regressed_score, regressed_detail = evaluate(golden_v1, regressed_model)
print(f"\n=== day 30: someone swapped the embedder -- re-run evaluate() ===")
print(f"new recall@3 = {regressed_score:.3f}  ({sum(regressed_detail.values())}/{len(golden_v1)} fully correct)")
REGRESSION_THRESHOLD = 0.10   # book/11: "คะแนนตก = รู้ทันที" -- any real drop counts
regression_flagged = (baseline_score - regressed_score) > REGRESSION_THRESHOLD
print(f"regression flagged: {regression_flagged}  (score dropped {baseline_score - regressed_score:.3f})")

# --- day 45: a real user query fails; it gets ADDED to the golden set ------
# (book/11 §11.5: "query ที่เคยค้นไม่เจอ → เพิ่มเข้าชุด → แกร่งขึ้นเรื่อยๆ")
new_failing_query = "งบประมาณเวิร์กช็อปปีนี้เท่าไหร่"
correct_doc_for_new_query = {"budget_note"}

golden_v2 = dict(golden_v1)   # golden sets only ever GROW, never shrink
golden_v2[new_failing_query] = correct_doc_for_new_query

fixed_model = make_search_engine({
    "อยากสอนเรื่อง AI ค้นหาข้อมูล": {"teaching_note", "ai_search_note"},
    "นัดหมายกับใครไว้บ้าง": {"meeting_note"},
    "สูตรกาแฟ": {"coffee_note"},
    new_failing_query: {"budget_note"},   # now fixed for the new query too
})
v2_score, v2_detail = evaluate(golden_v2, fixed_model)
print(f"\n=== day 45: new failing query added -> golden_v2 ({len(golden_v2)} queries) ===")
print(f"golden set grew: {len(golden_v1)} -> {len(golden_v2)} queries")
print(f"score on FULL golden_v2 (old + new) = {v2_score:.3f}")

# --- asserts -----------------------------------------------------------------
# 1. the baseline (good model, day 1) must score perfectly on its own golden set
assert baseline_score == 1.0, "the model the golden set was built to validate must score perfectly on it"

# 2. the regression (broken embedder swap) must score meaningfully lower --
#    otherwise this demo isn't actually simulating a real regression
assert regressed_score < baseline_score, "a regressed model must score lower than the recorded baseline"
assert regression_flagged, "a real quality drop must be FLAGGED by the regression-test threshold"

# 3. the golden set itself must only ever grow, never lose queries --
#    (book/11: "ข้อสอบโตได้") -- golden_v2 must be a strict superset of golden_v1
assert set(golden_v1.keys()) <= set(golden_v2.keys()), "growing the golden set must never remove existing queries"
assert len(golden_v2) == len(golden_v1) + 1, "adding one new failing query must grow the set by exactly one"

# 4. after fixing the bug AND growing the set, evaluate() on the FULL v2 set
#    (old queries + new one together) must score perfectly again
assert v2_score == 1.0, "after the fix, the fixed model must score perfectly on the FULL grown golden set"

# 5. evaluate() must always test the WHOLE current golden set, not just new
#    additions -- regression testing means re-checking everything, every time
_, full_recheck = evaluate(golden_v2, fixed_model)
assert all(full_recheck.values()), "regression testing must re-verify EVERY query in the set, old and new alike"

print("\n✓ all self-checks passed — build once, regression-test on every change, grow the set from real failures.")
