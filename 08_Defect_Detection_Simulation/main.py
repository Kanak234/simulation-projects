"""
MANUFACTURING DEFECT DETECTION SIMULATION
Single-file Monte-Carlo simulation of a four-station assembly line
with an automated inspection gate (sensitivity / specificity model),
rework loop, scrap decisions and quality-cost accounting.
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import random, os
from collections import Counter

random.seed(29)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
N_ITEMS = 2500
STATIONS = [("Cutting", 0.020), ("Machining", 0.032),
            ("Assembly", 0.048), ("Painting", 0.026)]
SENSITIVITY = 0.93        # P(flag | defective)
SPECIFICITY = 0.97        # P(pass | good)
REWORK_SUCCESS = 0.85
COST = {"inspect": 4, "rework": 60, "scrap": 350, "escape": 900}

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

src = Counter()
outcome = Counter()
TP = FP = TN = FN = 0
cost = 0.0

for _ in range(N_ITEMS):
    defect = None
    for st, p in STATIONS:
        if defect is None and random.random() < p:
            defect = st
    if defect:
        src[defect] += 1
    cost += COST["inspect"]
    if defect:
        if random.random() < SENSITIVITY:          # true positive
            TP += 1; cost += COST["rework"]
            if random.random() < REWORK_SUCCESS:
                outcome["Reworked OK"] += 1
            else:
                outcome["Scrapped"] += 1; cost += COST["scrap"]
        else:                                      # escaped defect
            FN += 1; outcome["Escaped defect"] += 1
            cost += COST["escape"]
    else:
        if random.random() < SPECIFICITY:          # true negative
            TN += 1; outcome["Good (direct)"] += 1
        else:                                      # false alarm
            FP += 1; outcome["False-flag rework"] += 1
            cost += COST["rework"]

defect_rate = 100 * (TP + FN) / N_ITEMS
recall = 100 * TP / max(1, TP + FN)
precision = 100 * TP / max(1, TP + FP)
good_out = outcome["Good (direct)"] + outcome["Reworked OK"] \
         + outcome["False-flag rework"]

print("=" * 58)
print(" MANUFACTURING DEFECT DETECTION SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Items produced      : {N_ITEMS}")
print(f" Defect rate         : {defect_rate:5.2f} %")
print(f" Detection recall    : {recall:5.1f} %   precision: {precision:5.1f} %")
print(f" Good units shipped  : {good_out}")
print(f" Escaped defects     : {outcome['Escaped defect']}")
print(f" Scrapped units      : {outcome['Scrapped']}")
print(f" Total quality cost  : Rs. {cost:,.0f} "
      f"(Rs. {cost/N_ITEMS:5.1f}/unit)")
for st, n in src.items():
    print(f"   defects from {st:<10}: {n}")

save_results({
    "Items produced": N_ITEMS,
    "True defect rate (%)": f"{defect_rate:.2f}",
    "Inspection recall (%)": f"{recall:.1f}",
    "Inspection precision (%)": f"{precision:.1f}",
    "Escaped defects (reached customer)": outcome["Escaped defect"],
    "Units scrapped": outcome["Scrapped"],
    "Total quality cost (Rs.)": f"{cost:,.0f}",
    "Quality cost per unit (Rs.)": f"{cost/N_ITEMS:.1f}",
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    plt.bar(src.keys(), src.values(), color="#c0392b")
    plt.ylabel("Defects introduced")
    plt.title("Defect Sources by Line Station")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    keys = ["Good (direct)", "Reworked OK", "False-flag rework",
            "Scrapped", "Escaped defect"]
    plt.bar(keys, [outcome[k] for k in keys], color="#2c3e50")
    plt.ylabel("Units"); plt.xticks(rotation=18, ha="right")
    plt.title("Final Disposition of Produced Units")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
