"""
HOSPITAL EMERGENCY DEPARTMENT SIMULATION
Single-file discrete-event simulation of an emergency department with
triage-based priority queues, limited doctors and beds.
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import heapq, random, os

random.seed(7)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
SIM_HOURS   = 12                 # length of simulated shift
DOCTORS     = 4                  # doctors on duty
BEDS        = 12                 # treatment beds
HOURLY_ARRIVALS = [6,8,10,14,16,18,20,17,14,12,9,7]   # patients/hour
SEVERITY_WEIGHTS = [5,12,28,35,20]                    # level 1..5
SERVICE_MEAN = {1:50, 2:38, 3:26, 4:18, 5:12}         # minutes

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

# ----------------------- ARRIVAL GENERATION ------------------
def generate_arrivals():
    events, pid = [], 0
    for h in range(SIM_HOURS):
        rate = HOURLY_ARRIVALS[h] / 60.0
        t = h * 60
        while True:
            t += random.expovariate(rate)
            if t >= (h + 1) * 60:
                break
            sev = random.choices([1,2,3,4,5], SEVERITY_WEIGHTS)[0]
            pid += 1
            events.append((t, pid, "arr", sev))
    return events

# ----------------------- SIMULATION ENGINE -------------------
def run():
    heap = generate_arrivals()
    heapq.heapify(heap)
    free_doc, free_bed = DOCTORS, BEDS
    waiting = []                       # (severity, arrival_time, pid)
    served, qlog = [], []
    busy_min, last_t = 0.0, 0.0
    seq = 10 ** 6

    def start(sev, arr, now):
        nonlocal free_doc, free_bed, seq
        free_doc -= 1; free_bed -= 1; seq += 1
        served.append((sev, now - arr))
        fin = now + random.expovariate(1.0 / SERVICE_MEAN[sev])
        heapq.heappush(heap, (fin, seq, "fin", sev))

    while heap:
        t, pid, kind, sev = heapq.heappop(heap)
        busy_min += (t - last_t) * (DOCTORS - free_doc)
        last_t = t
        if kind == "arr":
            if free_doc > 0 and free_bed > 0:
                start(sev, t, t)
            else:
                heapq.heappush(waiting, (sev, t, pid))
        else:                                   # treatment finished
            free_doc += 1; free_bed += 1
            if waiting:
                s, arr, _ = heapq.heappop(waiting)
                start(s, arr, t)
        qlog.append((t / 60.0, len(waiting)))
    return served, qlog, busy_min, len(waiting)

served, qlog, busy_min, still_wait = run()

# ----------------------- METRICS -----------------------------
by_sev = {s: [] for s in range(1, 6)}
for s, w in served:
    by_sev[s].append(w)
avg_by_sev = {s: (sum(v)/len(v) if v else 0.0) for s, v in by_sev.items()}
all_waits = [w for _, w in served]
avg_wait = sum(all_waits) / len(all_waits)
util = 100.0 * busy_min / (DOCTORS * SIM_HOURS * 60)
max_q = max(q for _, q in qlog)

print("=" * 58)
print(" HOSPITAL EMERGENCY DEPARTMENT SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Patients treated        : {len(served)}")
print(f" Average waiting time    : {avg_wait:6.1f} min")
for s in range(1, 6):
    print(f"   Severity {s} avg wait   : {avg_by_sev[s]:6.1f} min "
          f"({len(by_sev[s])} patients)")
print(f" Doctor utilisation      : {util:6.1f} %")
print(f" Maximum queue length    : {max_q}")

save_results({
    "Patients treated": len(served),
    "Average waiting time (min)": f"{avg_wait:.1f}",
    "Severity-1 (critical) avg wait (min)": f"{avg_by_sev[1]:.1f}",
    "Severity-5 (minor) avg wait (min)": f"{avg_by_sev[5]:.1f}",
    "Doctor utilisation (%)": f"{util:.1f}",
    "Maximum queue length": max_q,
})

# ----------------------- CHARTS ------------------------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    plt.bar([str(s) for s in range(1, 6)],
            [avg_by_sev[s] for s in range(1, 6)], color="#c0392b")
    plt.xlabel("Triage severity (1 = critical)"); plt.ylabel("Avg wait (min)")
    plt.title("Average Waiting Time by Triage Severity")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.step([x for x, _ in qlog], [q for _, q in qlog], where="post")
    plt.xlabel("Time (hours)"); plt.ylabel("Patients waiting")
    plt.title("Waiting-Room Queue Length Over the Shift")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
