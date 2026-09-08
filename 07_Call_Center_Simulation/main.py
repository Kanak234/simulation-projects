"""
TELECOM CALL CENTER SIMULATION
Single-file discrete-event simulation of an inbound call centre with a
time-varying call arrival profile, a finite agent pool, caller
abandonment and a 20-second service-level agreement (SLA).
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import heapq, random, os

random.seed(17)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
AGENTS   = 10
HOURS    = 8
HOURLY_CALLS = [90, 130, 170, 190, 180, 150, 120, 95]
AHT_MEAN     = 235.0          # average handling time (s)
PATIENCE_MEAN = 100.0         # mean caller patience (s)
SLA_SEC      = 20.0           # answer target

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

heap, cid = [], 0
for h in range(HOURS):
    rate = HOURLY_CALLS[h] / 3600.0
    t = h * 3600.0
    while True:
        t += random.expovariate(rate)
        if t >= (h + 1) * 3600:
            break
        cid += 1
        heapq.heappush(heap, (t, cid, "arr"))

free = AGENTS
queue, calls = [], {}
qlog = []
hour_offered  = [0]*HOURS
hour_answered = [0]*HOURS
hour_sla      = [0]*HOURS
hour_abandon  = [0]*HOURS
waits = []
busy, last_t = 0.0, 0.0
seq = 10 ** 7

def answer(c, now):
    global free, seq
    free -= 1
    w = now - c["arr"]; waits.append(w)
    h = min(HOURS-1, int(c["arr"] // 3600))
    hour_answered[h] += 1
    if w <= SLA_SEC:
        hour_sla[h] += 1
    seq += 1
    heapq.heappush(heap, (now + random.expovariate(1/AHT_MEAN), seq, "dep"))

while heap:
    t, i, kind = heapq.heappop(heap)
    busy += (t - last_t) * (AGENTS - free); last_t = t
    if kind == "arr":
        h = min(HOURS-1, int(t // 3600))
        hour_offered[h] += 1
        c = {"arr": t, "gone": False, "start": False}
        calls[i] = c
        if free > 0:
            c["start"] = True; answer(c, t)
        else:
            queue.append(c)
            seq += 1
            heapq.heappush(heap,
                (t + random.expovariate(1/PATIENCE_MEAN), i, "abn"))
    elif kind == "abn":
        c = calls.get(i)
        if c and not c["start"] and not c["gone"]:
            c["gone"] = True
            h = min(HOURS-1, int(c["arr"] // 3600))
            hour_abandon[h] += 1
    else:                                          # call finished
        free += 1
        while queue:
            c = queue.pop(0)
            if c["gone"]:
                continue
            c["start"] = True; answer(c, t); break
    qlog.append((t/3600, sum(1 for c in queue if not c["gone"])))

offered  = sum(hour_offered)
answered = sum(hour_answered)
abandoned = sum(hour_abandon)
sl = 100 * sum(hour_sla) / max(1, answered)
avg_wait = sum(waits)/len(waits)
occ = 100 * busy / (AGENTS * HOURS * 3600)

print("=" * 58)
print(" TELECOM CALL CENTER SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Calls offered      : {offered}")
print(f" Calls answered     : {answered}")
print(f" Calls abandoned    : {abandoned} "
      f"({100*abandoned/offered:4.1f} %)")
print(f" Service level      : {sl:4.1f} % answered within {SLA_SEC:.0f}s")
print(f" Avg answer wait    : {avg_wait:5.1f} s")
print(f" Agent occupancy    : {occ:4.1f} %")

save_results({
    "Calls offered": offered,
    "Calls answered": answered,
    "Abandonment rate (%)": f"{100*abandoned/offered:.1f}",
    "Service level within 20 s (%)": f"{sl:.1f}",
    "Average answer wait (s)": f"{avg_wait:.1f}",
    "Agent occupancy (%)": f"{occ:.1f}",
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sl_hour = [100*hour_sla[h]/max(1, hour_answered[h]) for h in range(HOURS)]
    plt.figure(figsize=(7, 4))
    plt.bar([f"H{h+1}" for h in range(HOURS)], sl_hour, color="#e67e22")
    plt.axhline(80, color="red", ls="--", lw=0.9, label="80 % target")
    plt.ylabel("Service level (%)"); plt.ylim(0, 100); plt.legend()
    plt.title("Hourly Service Level (answered within 20 s)")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.step([x for x, _ in qlog], [q for _, q in qlog],
             where="post", lw=0.8, color="#34495e")
    plt.xlabel("Time (hours)"); plt.ylabel("Callers waiting")
    plt.title("Call Queue Length Over the Day")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
