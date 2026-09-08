"""
AGRICULTURE IRRIGATION SCHEDULING SIMULATION
Single-file day-stepped soil-moisture simulation for multiple crop
fields sharing a limited daily water budget. The scheduler irrigates
the driest fields first (deficit-priority allocation).
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import math, random, os

random.seed(21)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
DAYS = 45
TAW = 100.0                 # total available water in root zone (mm)
TARGET, CRITICAL = 80.0, 35.0          # moisture set-points (%)
DAILY_BUDGET = 180.0        # mm x ha of water available per day
EVENT_CAP = 25.0            # max mm applied to a field per day
FIELDS = [                  # name, area (ha), crop coefficient Kc
    ("Wheat", 2.0, 1.15), ("Maize", 1.5, 1.05),
    ("Vegetables", 1.0, 0.95), ("Sugarcane", 2.5, 1.25),
    ("Pulses", 1.2, 0.85),
]

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

moist = {f[0]: 70.0 for f in FIELDS}
hist = {f[0]: [] for f in FIELDS}
water_day, total_water = [], 0.0
stress_days = rain_days = 0

for d in range(DAYS):
    et0 = max(2.0, 5 + 1.5 * math.sin(2*math.pi*d/45) + random.gauss(0, 0.6))
    rain = random.uniform(4, 28) if random.random() < 0.22 else 0.0
    if rain:
        rain_days += 1
    # ---- deplete / recharge soil moisture -----------------------
    for name, area, kc in FIELDS:
        etc = kc * et0                              # crop water use (mm)
        moist[name] += (rain - etc) / TAW * 100
        moist[name] = max(0.0, min(100.0, moist[name]))
    # ---- deficit-priority irrigation ----------------------------
    budget = DAILY_BUDGET
    used = 0.0
    for name, area, kc in sorted(FIELDS, key=lambda f: moist[f[0]]):
        if moist[name] >= TARGET or budget <= 0:
            continue
        need_mm = (TARGET - moist[name]) / 100 * TAW
        apply_mm = min(EVENT_CAP, need_mm, budget / area)
        moist[name] += apply_mm / TAW * 100
        budget -= apply_mm * area
        used += apply_mm * area
    total_water += used
    water_day.append(used)
    for name, *_ in FIELDS:
        hist[name].append(moist[name])
        if moist[name] < CRITICAL:
            stress_days += 1

avg_final = sum(moist.values()) / len(moist)
print("=" * 58)
print(" IRRIGATION SCHEDULING SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Water applied (total)  : {total_water:7.1f} mm-ha")
print(f" Rain days              : {rain_days}")
print(f" Crop stress field-days : {stress_days}")
print(f" Avg final moisture     : {avg_final:5.1f} %")
for n in moist:
    print(f"   {n:<10}: final moisture {moist[n]:5.1f} %")

save_results({
    "Water applied over season (mm-ha)": f"{total_water:.1f}",
    "Rain days in season": rain_days,
    "Crop stress field-days (<35%)": stress_days,
    "Average final soil moisture (%)": f"{avg_final:.1f}",
    "Fields managed": len(FIELDS),
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    for n, series in hist.items():
        plt.plot(range(DAYS), series, label=n, lw=1.1)
    plt.axhline(CRITICAL, color="red", ls="--", lw=0.8, label="Stress line")
    plt.xlabel("Day"); plt.ylabel("Soil moisture (%)"); plt.ylim(0, 100)
    plt.title("Soil Moisture per Field"); plt.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.bar(range(DAYS), water_day, color="#2980b9")
    plt.xlabel("Day"); plt.ylabel("Water applied (mm-ha)")
    plt.title("Daily Irrigation Water Consumption")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
