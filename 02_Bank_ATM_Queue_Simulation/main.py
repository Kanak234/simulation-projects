"""
BANK ATM QUEUE MANAGEMENT SIMULATION
Single-file M/M/c queueing simulation of an ATM lobby with customer
impatience (reneging) and balking when the queue is too long.
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import heapq, random, os

random.seed(11)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
ATMS          = 3
SIM_MIN       = 480                          # 8-hour banking day
HOURLY_RATE   = [40,55,75,90,80,60,50,70]    # customers per hour
SERVICE_MEAN  = 2.4                          # minutes per transaction
PATIENCE      = (3.0, 9.0)                   # uniform patience (min)
BALK_QUEUE    = 12                           # customer walks away

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

# ----------------------- EVENT GENERATION --------------------
heap, cid = [], 0
for h in range(8):
    rate = HOURLY_RATE[h] / 60.0
    t = h * 60
    while True:
        t += random.expovariate(rate)
        if t >= (h + 1) * 60:
            break
        cid += 1
        heapq.heappush(heap, (t, cid, "arr"))

# ----------------------- SIMULATION --------------------------
free = ATMS
queue = []                       # list of dicts
cust = {}
waits, qlog = [], []
served = reneged = balked = 0
busy_min, last_t = 0.0, 0.0
seq = 10 ** 6

def begin_service(c, now):
    global free, seq, served
    free -= 1; served += 1
    waits.append(now - c["arr"])
    seq += 1
    heapq.heappush(heap, (now + random.expovariate(1 / SERVICE_MEAN),
                          seq, "dep"))

while heap:
    t, i, kind = heapq.heappop(heap)
    busy_min += (t - last_t) * (ATMS - free); last_t = t
    if kind == "arr":
        c = {"id": i, "arr": t, "gone": False, "start": False}
        cust[i] = c
        if free > 0:
            c["start"] = True; begin_service(c, t)
        elif len(queue) >= BALK_QUEUE:
            balked += 1
        else:
            queue.append(c)
            seq += 1
            heapq.heappush(heap, (t + random.uniform(*PATIENCE), i, "ren"))
    elif kind == "ren":
        c = cust.get(i)
        if c and not c["start"] and not c["gone"]:
            c["gone"] = True; reneged += 1
    else:                                        # departure
        free += 1
        while queue:
            c = queue.pop(0)
            if c["gone"]:
                continue
            c["start"] = True; begin_service(c, t); break
    qlog.append((t, sum(1 for c in queue if not c["gone"])))

avg_wait = sum(waits) / len(waits)
waits_sorted = sorted(waits)
p90 = waits_sorted[int(0.9 * len(waits_sorted))]
util = 100 * busy_min / (ATMS * SIM_MIN)
max_q = max(q for _, q in qlog)

print("=" * 58)
print(" BANK ATM QUEUE MANAGEMENT SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Customers served      : {served}")
print(f" Reneged (impatient)   : {reneged}")
print(f" Balked (queue full)   : {balked}")
print(f" Average wait          : {avg_wait:5.2f} min")
print(f" 90th percentile wait  : {p90:5.2f} min")
print(f" ATM utilisation       : {util:5.1f} %")
print(f" Maximum queue length  : {max_q}")

save_results({
    "Customers served": served,
    "Customers reneged (impatient)": reneged,
    "Customers balked (queue full)": balked,
    "Average waiting time (min)": f"{avg_wait:.2f}",
    "90th percentile wait (min)": f"{p90:.2f}",
    "ATM utilisation (%)": f"{util:.1f}",
    "Maximum queue length": max_q,
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    plt.step([x/60 for x, _ in qlog], [q for _, q in qlog], where="post",
             color="#16a085")
    plt.xlabel("Time (hours)"); plt.ylabel("Customers in queue")
    plt.title("ATM Lobby Queue Length Over the Day")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.hist(waits, bins=24, color="#2980b9", edgecolor="white")
    plt.xlabel("Waiting time (min)"); plt.ylabel("Customers")
    plt.title("Distribution of Customer Waiting Times")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
