"""Dig-loop 42/50 — Leaderboard overfitting: the MTEB winner isn't always YOUR winner.

Grounded in deep-technical/39-evaluation-datasets.md §39.4 (a model can be
tuned to win MTEB/BEIR specifically -- trained on data similar to the
leaderboard's own test sets -- scoring high there while NOT generalizing to
a genuinely different domain/language) and §39.7/§39.5 ("อย่าเชื่อ leaderboard
rank เดียว" -- คะแนนอังกฤษดีไม่การันตีไทยดี -- the real fix is measuring nDCG@10
on YOUR OWN task, never trusting the public rank alone).
Runnable standalone (stdlib only):  python iter-42-pooled-judgment.py

Reuses iter-21's nDCG implementation to make the leaderboard-vs-own-task
divergence concrete and provable: a model that tops the public leaderboard
can genuinely lose on your real deployment task.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def dcg(rels):
    return sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels))


def ndcg(rels):
    ideal = sorted(rels, reverse=True)
    idcg = dcg(ideal)
    return dcg(rels) / idcg if idcg > 0 else 0.0


# --- Model X: heavily tuned to win the public leaderboard (train data
#     resembles MTEB/BEIR's own test distribution -- §39.4's real risk) ----
MODEL_X_ON_LEADERBOARD = [3, 3, 2, 3, 2]   # excellent -- this IS its training distribution
MODEL_X_ON_OWN_TASK = [0, 1, 0, 0, 1]       # poor -- genuinely different domain/language (Thai)

# --- Model Y: robustly multilingual (bge-m3-like), not leaderboard-tuned --
MODEL_Y_ON_LEADERBOARD = [2, 2, 1, 2, 1]   # decent, not top
MODEL_Y_ON_OWN_TASK = [3, 2, 3, 2, 3]       # excellent -- genuinely generalizes to YOUR task

ndcg_x_leaderboard = ndcg(MODEL_X_ON_LEADERBOARD)
ndcg_x_own = ndcg(MODEL_X_ON_OWN_TASK)
ndcg_y_leaderboard = ndcg(MODEL_Y_ON_LEADERBOARD)
ndcg_y_own = ndcg(MODEL_Y_ON_OWN_TASK)

print("=== §39.4: leaderboard nDCG@5 vs YOUR OWN TASK nDCG@5 ===")
print(f"Model X (leaderboard-tuned)  leaderboard nDCG = {ndcg_x_leaderboard:.3f}   own-task nDCG = {ndcg_x_own:.3f}")
print(f"Model Y (robust multilingual) leaderboard nDCG = {ndcg_y_leaderboard:.3f}   own-task nDCG = {ndcg_y_own:.3f}")

leaderboard_winner = "Model X" if ndcg_x_leaderboard > ndcg_y_leaderboard else "Model Y"
own_task_winner = "Model X" if ndcg_x_own > ndcg_y_own else "Model Y"

print(f"\nleaderboard rank says: {leaderboard_winner} wins")
print(f"your own task says:    {own_task_winner} wins")
print(f"\nif you trusted the leaderboard rank alone and picked {leaderboard_winner},")
print(f"your REAL deployment would score nDCG={ndcg_x_own if leaderboard_winner=='Model X' else ndcg_y_own:.3f}")
print(f"instead of the {own_task_winner}'s {max(ndcg_x_own, ndcg_y_own):.3f} -- a real, measurable loss")

# --- the correct decision rule (§39.7): always measure on YOUR OWN task ----
def pick_model_by(scores_dict):
    return max(scores_dict, key=scores_dict.get)


own_task_scores = {"Model X": ndcg_x_own, "Model Y": ndcg_y_own}
leaderboard_scores = {"Model X": ndcg_x_leaderboard, "Model Y": ndcg_y_leaderboard}
correct_choice = pick_model_by(own_task_scores)
naive_choice = pick_model_by(leaderboard_scores)

print(f"\ndecision rule 'trust the leaderboard' picks: {naive_choice}")
print(f"decision rule 'measure your own task' picks:  {correct_choice}")

# --- asserts -----------------------------------------------------------------
# 1. Model X must genuinely win the public leaderboard -- the overfitting
#    is real, not a strawman
assert ndcg_x_leaderboard > ndcg_y_leaderboard, \
    "Model X must genuinely score higher on the public leaderboard (that's the whole point of leaderboard-tuning)"

# 2. Model Y must genuinely win on the real, own-domain task -- the
#    leaderboard winner is NOT the real winner for actual deployment
assert ndcg_y_own > ndcg_x_own, \
    "Model Y must genuinely score higher on the real own-task benchmark despite losing the public leaderboard"

# 3. the leaderboard-driven choice and the own-task-driven choice must
#    DISAGREE -- this is the actual danger the book warns about
assert naive_choice != correct_choice, \
    "trusting the leaderboard alone must lead to a DIFFERENT (and wrong) model choice than measuring your own task"

# 4. quantify the real cost: picking the leaderboard winner instead of the
#    own-task winner must cost a measurable nDCG loss on real deployment
real_cost = ndcg_y_own - ndcg_x_own
assert real_cost > 0.3, \
    "the nDCG gap between the correct choice and the leaderboard-driven mistake must be substantial, not negligible"

# 5. sanity: nDCG values must all be valid [0, 1]
for v in (ndcg_x_leaderboard, ndcg_x_own, ndcg_y_leaderboard, ndcg_y_own):
    assert 0.0 <= v <= 1.0

print("\n✓ all self-checks passed — the leaderboard winner is not always YOUR winner; always measure nDCG on your own task before choosing.")
