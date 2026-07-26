"""Dig-loop 43/50 — Batching: the real cure for embed throughput (not latency).

Grounded in deep-technical/44-latency-optimization.md §44.1 (embed is THE
bottleneck: ~30-80ms per query, the single biggest latency line) and §44.3
(real numbers: 1 query = 1 GPU call = 30ms = 33 qps; batch 32 queries = 1
GPU call = 50ms = 640 qps -- 19x throughput, because GPU matrix math makes
batching almost free) plus the honest caveat: dynamic batching trades a
SMALL latency increase (wait up to 5ms for the batch to fill) for a BIG
throughput gain -- but only when queries arrive fast enough to fill a batch;
a single-user local setup (ARRA) rarely benefits.
Runnable standalone (stdlib only):  python iter-43-batch-embed-cure.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""

# --- book/44 §44.3's exact real numbers, modeled as a linear cost function --
# cost(n) = fixed_overhead + per_item * n, solved to hit cost(1)=30, cost(32)=50
PER_ITEM = 20 / 31
FIXED_OVERHEAD = 30 - PER_ITEM


def gpu_call_cost_ms(n):
    return FIXED_OVERHEAD + PER_ITEM * n


cost_1 = gpu_call_cost_ms(1)
cost_32 = gpu_call_cost_ms(32)
throughput_single = 1000 / cost_1            # queries per second, batch size 1
throughput_batched = 32 * 1000 / cost_32      # queries per second, batch size 32
speedup = throughput_batched / throughput_single

print("=== §44.3: batching throughput math ===")
print(f"1 query/call:  {cost_1:.1f}ms -> {throughput_single:.1f} qps")
print(f"32 queries/call: {cost_32:.1f}ms -> {throughput_batched:.1f} qps")
print(f"throughput speedup = {speedup:.1f}x")


# --- dynamic batching simulation: collect until batch full OR wait_max ------
def simulate_dynamic_batching(arrival_gap_ms, batch_max=32, wait_max_ms=5, n_queries=200):
    """arrival_gap_ms: time between consecutive query arrivals.
    Returns (avg_added_latency_ms, effective_avg_batch_size, throughput_qps)."""
    arrivals = [i * arrival_gap_ms for i in range(n_queries)]
    completions = []
    batch_sizes = []
    i = 0
    clock = 0.0
    while i < n_queries:
        batch_start_arrival = arrivals[i]
        clock = max(clock, batch_start_arrival)
        batch = [i]
        j = i + 1
        while j < n_queries and len(batch) < batch_max and (arrivals[j] - batch_start_arrival) <= wait_max_ms:
            batch.append(j)
            j += 1
        # the batch "fires" either when full, or after waiting wait_max_ms
        fire_time = max(clock, batch_start_arrival) + (0 if len(batch) == batch_max else wait_max_ms)
        fire_time = max(fire_time, arrivals[batch[-1]])   # can't fire before the last member arrives
        finish_time = fire_time + gpu_call_cost_ms(len(batch))
        for idx in batch:
            completions.append(finish_time - arrivals[idx])   # total latency incl. wait
        batch_sizes.append(len(batch))
        clock = finish_time
        i = j

    avg_latency = sum(completions) / len(completions)
    avg_batch_size = sum(batch_sizes) / len(batch_sizes)
    total_time_s = (clock - arrivals[0]) / 1000
    throughput = n_queries / total_time_s
    return avg_latency, avg_batch_size, throughput


# --- HIGH arrival rate: queries pour in fast -> batches fill up, real gain --
high_latency, high_batch_size, high_throughput = simulate_dynamic_batching(arrival_gap_ms=0.1)

# --- LOW arrival rate (ARRA single-user local): queries trickle in slowly,
#     nowhere near fast enough to fill a batch within wait_max_ms ----------
low_latency, low_batch_size, low_throughput = simulate_dynamic_batching(arrival_gap_ms=200)

print(f"\n=== dynamic batching (wait <= 5ms or batch=32) under different loads ===")
print(f"HIGH arrival rate (busy server): avg batch size={high_batch_size:.1f}, "
      f"avg latency={high_latency:.1f}ms, throughput={high_throughput:.0f} qps")
print(f"LOW arrival rate (ARRA single-user): avg batch size={low_batch_size:.1f}, "
      f"avg latency={low_latency:.1f}ms, throughput={low_throughput:.0f} qps")
print(f"\nlesson (§44.3): batching only pays off when queries arrive fast enough to")
print(f"actually fill a batch -- single-user local (ARRA) rarely benefits from this knob")

# --- asserts -----------------------------------------------------------------
# 1. the cost model must reproduce the book's exact real numbers
assert abs(cost_1 - 30.0) < 0.01, "cost(1) must match the book's real 30ms figure"
assert abs(cost_32 - 50.0) < 0.01, "cost(32) must match the book's real 50ms figure"

# 2. throughput speedup must match the book's real ~19x claim
assert 18.0 < speedup < 20.0, "batching throughput speedup must be close to the book's real ~19x figure"

# 3. under a busy (high-arrival-rate) load, batches must actually fill up
#    near the max size -- the real precondition for throughput gains
assert high_batch_size > 25, "under high query arrival rate, batches must fill up close to the max size"

# 4. throughput under high load must be dramatically higher than under low
#    load -- batching genuinely pays off when there's enough traffic
assert high_throughput > 10 * low_throughput, \
    "batched throughput under high load must be dramatically higher than under sparse load"

# 5. under LOW arrival rate (single-user local), batches must stay tiny --
#    proving the book's caveat that ARRA rarely benefits from this knob
assert low_batch_size < 1.5, \
    "under low query arrival rate, average batch size must stay near 1 (no real batching happens)"

# 6. under sustained heavy load, throughput must approach the theoretical
#    batch-32 ceiling computed in §44.3 -- the system saturates AT that
#    ceiling (queueing delay grows under oversubscription, which is the
#    real, expected trade of pushing traffic past a fixed batch's capacity)
assert high_throughput > throughput_batched * 0.85, \
    "under sustained heavy load, achieved throughput must approach the theoretical batch-32 ceiling"

print("\n✓ all self-checks passed — batching gives real ~19x throughput ONLY when traffic is dense enough to fill a batch.")
