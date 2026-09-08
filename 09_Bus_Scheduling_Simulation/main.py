"""
PUBLIC TRANSPORT BUS SCHEDULING SIMULATION
Single-file simulation of a circular city bus route (8 stops) with a
small fleet, passenger arrivals at stops, boarding / alighting,
capacity limits, headway offsets and fuel accounting.
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import random, os

random.seed(31)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
STOPS = ["Jhanda Chowk", "Guru Gobind Singh Rd", "Korrah", "Matwari",
         "Bus Stand", "Annada Chowk", "Lake Road", "Kalibari"]
SEG_KM  = [1.1, 0.9, 1.3, 1.0, 1.2, 0.8, 1.4, 1.0]   # to next stop
ARR_MIN = [1.4, 1.0, 1.8, 1.3, 2.2, 1.6, 0.9, 1.1]   # pax/min per stop
BUSES = 4
CAPACITY = 50
SPEED_KMPH = 24
SIM_MIN = 180
ALIGHT_P = 0.27
DWELL_PER_PAX = 0.05        # minutes
FUEL_PER_KM = 0.34          # litres

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

def poisson(lam):
    import math
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= random.random()
        if p <= L:
            return k
        k += 1

seg_time = [d / SPEED_KMPH * 60 for d in SEG_KM]
stop_q = [[] for _ in STOPS]                 # arrival timestamps
buses = [{"stop": (i * 2) % len(STOPS),
          "next_t": i * 3.0, "on": 0, "km": 0.0}
         for i in range(BUSES)]
waits_by_stop = [[] for _ in STOPS]
bus0_load = []
served = leftover = 0
fuel = 0.0

for minute in range(SIM_MIN):
    # passengers arrive at every stop
    for s in range(len(STOPS)):
        for _ in range(poisson(ARR_MIN[s])):
            stop_q[s].append(minute + random.random())
    # move buses
    for bi, b in enumerate(buses):
        while b["next_t"] <= minute:
            s = b["stop"]
            alight = min(b["on"], poisson(b["on"] * ALIGHT_P))
            b["on"] -= alight
            board = 0
            while stop_q[s] and b["on"] < CAPACITY:
                arr = stop_q[s].pop(0)
                waits_by_stop[s].append(max(0.0, b["next_t"] - arr))
                b["on"] += 1; board += 1; served += 1
            dwell = DWELL_PER_PAX * (alight + board)
            b["km"] += SEG_KM[s]
            fuel += SEG_KM[s] * FUEL_PER_KM
            b["next_t"] += dwell + seg_time[s]
            b["stop"] = (s + 1) % len(STOPS)
            if bi == 0:
                bus0_load.append((b["next_t"], b["on"]))

leftover = sum(len(q) for q in stop_q)
all_waits = [w for ws in waits_by_stop for w in ws]
avg_wait = sum(all_waits) / len(all_waits)
avg_stop_wait = [ (sum(w)/len(w) if w else 0.0) for w in waits_by_stop ]
km_total = sum(b["km"] for b in buses)
load_samples = [l for _, l in bus0_load]
avg_load = 100 * sum(load_samples) / (len(load_samples) * CAPACITY)

print("=" * 58)
print(" PUBLIC TRANSPORT BUS SCHEDULING SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Passengers served    : {served}")
print(f" Still waiting at end : {leftover}")
print(f" Average wait         : {avg_wait:5.2f} min")
print(f" Fleet distance       : {km_total:6.1f} km")
print(f" Fuel consumed        : {fuel:6.1f} L")
print(f" Avg load factor (bus 1): {avg_load:5.1f} %")

save_results({
    "Passengers served (3 h)": served,
    "Passengers left waiting": leftover,
    "Average passenger wait (min)": f"{avg_wait:.2f}",
    "Fleet distance covered (km)": f"{km_total:.1f}",
    "Fuel consumed (L)": f"{fuel:.1f}",
    "Average load factor (%)": f"{avg_load:.1f}",
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4.2))
    plt.bar(STOPS, avg_stop_wait, color="#16a085")
    plt.ylabel("Avg wait (min)"); plt.xticks(rotation=30, ha="right")
    plt.title("Average Passenger Waiting Time per Stop")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.plot([t for t, _ in bus0_load], [l for _, l in bus0_load],
             marker=".", lw=0.9, color="#8e44ad")
    plt.axhline(CAPACITY, color="red", ls="--", lw=0.8, label="Capacity")
    plt.xlabel("Time (min)"); plt.ylabel("Passengers on board")
    plt.title("Bus 1 Occupancy Along the Route"); plt.legend()
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
