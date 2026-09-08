"""
LIBRARY BOOK CIRCULATION SIMULATION
Single-file day-stepped simulation of a college library: borrowing,
returns, late fines, unmet reservations and a 7-day moving-average
demand forecast.
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import math, random, os
from collections import defaultdict

random.seed(13)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
DAYS = 60
LOAN_DAYS = 7
FINE_PER_DAY = 2                      # rupees
CATEGORIES = {                        # copies, base demand/day
    "Programming":       (40, 9),
    "Science":           (35, 7),
    "Literature":        (30, 6),
    "Competitive Exams": (25, 8),
    "Comics":            (20, 5),
}

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

def poisson(lam):
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= random.random()
        if p <= L:
            return k
        k += 1

available = {c: n for c, (n, _) in CATEGORIES.items()}
returns = defaultdict(list)           # day -> [(cat, late_days)]
daily_total, ma_forecast = [], []
borrows_by_cat = defaultdict(int)
fines = unmet = total_borrows = 0

for d in range(DAYS):
    # ---- process today's returns -------------------------------
    for cat, late in returns[d]:
        available[cat] += 1
        fines += late * FINE_PER_DAY
    # ---- new demand ---------------------------------------------
    season = 1 + 0.3 * math.sin(2 * math.pi * d / 30)
    today = 0
    for cat, (copies, base) in CATEGORIES.items():
        for _ in range(poisson(base * season)):
            if available[cat] > 0:
                available[cat] -= 1
                late = random.choice([0]*3 + [random.randint(1, 5)])
                returns[d + LOAN_DAYS + late].append((cat, late))
                borrows_by_cat[cat] += 1
                today += 1
            else:
                unmet += 1
    total_borrows += today
    daily_total.append(today)
    window = daily_total[-7:]
    ma_forecast.append(sum(window) / len(window))

# forecast accuracy (MA of previous day vs actual, day 8 onwards)
errs = [abs(daily_total[i] - ma_forecast[i-1]) / max(1, daily_total[i])
        for i in range(8, DAYS)]
mape = 100 * sum(errs) / len(errs)

print("=" * 58)
print(" LIBRARY BOOK CIRCULATION SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Total books issued        : {total_borrows}")
print(f" Fines collected           : Rs. {fines}")
print(f" Unmet reservations        : {unmet}")
print(f" Forecast error (MAPE)     : {mape:4.1f} %")
for c, n in borrows_by_cat.items():
    print(f"   {c:<18}: {n} issues")

save_results({
    "Total books issued (60 days)": total_borrows,
    "Fines collected (Rs.)": fines,
    "Unmet reservations": unmet,
    "Most demanded category": max(borrows_by_cat, key=borrows_by_cat.get),
    "7-day MA forecast error (MAPE %)": f"{mape:.1f}",
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    plt.plot(range(DAYS), daily_total, label="Actual issues", lw=1)
    plt.plot(range(DAYS), ma_forecast, label="7-day MA forecast", lw=1.6)
    plt.xlabel("Day"); plt.ylabel("Books issued")
    plt.title("Daily Circulation vs Moving-Average Forecast"); plt.legend()
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.bar(borrows_by_cat.keys(), borrows_by_cat.values(), color="#27ae60")
    plt.ylabel("Issues"); plt.xticks(rotation=20, ha="right")
    plt.title("Issues by Category (60 days)")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
