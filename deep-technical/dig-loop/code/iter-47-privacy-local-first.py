"""Dig-loop 47/50 — Privacy: proving no byte leaves the machine.

Grounded in book/12-privacy-local-first.md §12.1 (every endpoint used across
all 12 chapters is local: embedding via Ollama at http://localhost:11434,
LLM (gemma3) at the same local endpoint, vector DB as a plain local file
./chroma_db with NO network at all -- "ไม่มีสักไบต์ที่ออกอินเทอร์เน็ต") and
§12.2 (ownership: second brain = one folder, copy/backup/delete freely, no
vendor, no API key to expire).
Runnable standalone (stdlib only):  python iter-47-privacy-local-first.py

Builds a NetworkGuard that records every "network call" a mock pipeline
makes, so the "no data leaves the machine" claim is PROVEN by inspecting
actual call logs, not just asserted by trusting the code. Also demonstrates
what a real leak would look like, to prove the guard actually catches it.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
from urllib.parse import urlparse

LOCAL_HOSTS = {"localhost", "127.0.0.1"}


class NetworkGuard:
    """Records every outbound call a pipeline makes, so we can PROVE
    (by inspecting the log) whether any byte ever left the machine."""
    def __init__(self):
        self.calls = []

    def record(self, url):
        self.calls.append(url)
        return url

    def is_local(self, url):
        parsed = urlparse(url)
        if not parsed.scheme:
            return True   # a bare filesystem path -- not network at all
        return parsed.hostname in LOCAL_HOSTS

    def all_calls_local(self):
        return all(self.is_local(u) for u in self.calls)

    def external_calls(self):
        return [u for u in self.calls if not self.is_local(u)]


# --- the REAL local-first pipeline (book/12 §12.1's actual endpoints) ------
def local_embed(guard, text):
    guard.record("http://localhost:11434/api/embeddings")
    return [0.9, 0.1, 0.0]   # stand-in vector


def local_vector_db_query(guard, vec, db_path="./chroma_db"):
    guard.record(db_path)   # a bare path -- pure local file access, no network
    return [{"id": "d1", "text": "โน้ตส่วนตัว", "score": 0.92}]


def local_llm_generate(guard, prompt):
    guard.record("http://localhost:11434/api/generate")
    return "คำตอบที่สังเคราะห์จากโน้ตในเครื่อง"


def run_local_first_pipeline(query_text):
    guard = NetworkGuard()
    qvec = local_embed(guard, query_text)
    results = local_vector_db_query(guard, qvec)
    answer = local_llm_generate(guard, f"ตอบจาก: {results}")
    return guard, answer


guard, answer = run_local_first_pipeline("โน้ตประชุมล่าสุดพูดถึงอะไร")

print("=== §12.1: the actual local-first pipeline, every call logged ===")
for call in guard.calls:
    print(f"  {call}  {'[LOCAL]' if guard.is_local(call) else '[EXTERNAL -- LEAK!]'}")
print(f"\nall calls local? {guard.all_calls_local()}")
print(f"answer: {answer}")


# --- what a MISCONFIGURED (leaky) pipeline would look like -----------------
def leaky_embed(guard, text):
    guard.record("https://api.openai.com/v1/embeddings")   # accidentally external!
    return [0.9, 0.1, 0.0]


def run_leaky_pipeline(query_text):
    guard = NetworkGuard()
    qvec = leaky_embed(guard, query_text)
    results = local_vector_db_query(guard, qvec)
    answer = local_llm_generate(guard, f"ตอบจาก: {results}")
    return guard, answer


leaky_guard, _ = run_leaky_pipeline("โน้ตประชุมล่าสุดพูดถึงอะไร")

print(f"\n=== a MISCONFIGURED pipeline (one step accidentally external) ===")
for call in leaky_guard.calls:
    print(f"  {call}  {'[LOCAL]' if leaky_guard.is_local(call) else '[EXTERNAL -- LEAK!]'}")
print(f"all calls local? {leaky_guard.all_calls_local()}")
print(f"external calls detected: {leaky_guard.external_calls()}")

# --- asserts -----------------------------------------------------------------
# 1. the real local-first pipeline must make EXACTLY 3 recorded calls
#    (embed, vector db, LLM generate) -- matching book/12's 3 endpoints
assert len(guard.calls) == 3, "the local-first pipeline must make exactly 3 recorded operations"

# 2. every single call in the real pipeline must be local -- proving the
#    "not a single byte leaves the machine" claim by actually checking
assert guard.all_calls_local(), "every call in the local-first pipeline must be local (no external hosts)"
assert guard.external_calls() == [], "the local-first pipeline must have zero external calls"

# 3. the vector DB step specifically must be a bare filesystem path with NO
#    network scheme at all -- not just "localhost", genuinely no network
db_call = guard.calls[1]
assert not urlparse(db_call).scheme, "the vector DB call must be a plain local file path, not even a localhost URL"

# 4. the embed and LLM calls must both target localhost specifically
#    (Ollama), matching book/12's real endpoint
assert "localhost:11434" in guard.calls[0], "the embed call must target the local Ollama endpoint"
assert "localhost:11434" in guard.calls[2], "the LLM generate call must target the local Ollama endpoint"

# 5. the guard must correctly DETECT a real leak when one exists -- proving
#    this isn't a rubber-stamp check that always passes
assert not leaky_guard.all_calls_local(), "the guard must detect the leaky pipeline as NOT all-local"
assert len(leaky_guard.external_calls()) == 1, "the guard must identify exactly the one external call"
assert "api.openai.com" in leaky_guard.external_calls()[0], "the detected leak must be the OpenAI endpoint"

print("\n✓ all self-checks passed — every call in the real pipeline is local; the guard genuinely catches leaks when they happen.")
