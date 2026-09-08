"""
RETAIL STORE INVENTORY MANAGEMENT SIMULATION
Single-file day-stepped inventory simulation for a kirana / retail
store: stochastic demand with weekend uplift, reorder-point policy,
supplier lead time, FIFO shelf-life expiry for perishables and full
cost accounting (holding, lost sales, expiry, ordering).
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import math, random, os
from collections import deque

random.seed(37)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
DAYS = 90
LEAD = 3
ORDER_COST = 30.0
HOLD_RATE = 0.0005        # of unit cost per unit per day
#         name          mean  price cost shelf  ROP  OQ
SKUS = [("Rice 5kg",       6,  320, 260, None,  22,  60),
        ("Milk 1L",       24,   58,  46,    4,  85,  90),
        ("Bread",         18,   45,  32,    3,  65,  60),
        ("Cooking Oil",    5,  190, 150, None,  17,  45),
        ("Biscuits",      12,   30,  20,  120,  40,  80),
        ("Eggs (dozen)",  10,   84,  66,   10,  40,  70)]
TRACK = ["Milk 1L", "Rice 5kg", "Bread"]

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

stock = {}
for s in SKUS:                      # opening stock lot
    exp0 = s[4] if s[4] is not None else None
    stock[s[0]] = deque([[s[6], exp0]])
pipeline = {s[0]: [] for s in SKUS}
series = {t: [] for t in TRACK}
hold_c = lost_c = exp_c = ord_c = revenue = 0.0
demand_tot = fulfilled = waste_units = orders = 0

for d in range(DAYS):
    weekend = 1.35 if d % 7 in (5, 6) else 1.0
    for name, mean, price, ucost, shelf, rop, oq in SKUS:
        lots = stock[name]
        # receive arrivals
        arrived = [q for ad, q in pipeline[name] if ad == d]
        pipeline[name] = [(ad, q) for ad, q in pipeline[name] if ad > d]
        for q in arrived:
            lots.append([q, d + shelf if shelf is not None else None])
        # expiry (FIFO lots)
        while lots and lots[0][1] is not None and lots[0][1] <= d:
            q, _ = lots.popleft()
            waste_units += q; exp_c += q * ucost
        # demand
        dem = poisson(mean * weekend)
        demand_tot += dem
        need = dem
        while need and lots:
            take = min(need, lots[0][0])
            lots[0][0] -= take; need -= take
            fulfilled += take; revenue += take * price
            if lots[0][0] == 0:
                lots.popleft()
        if need:
            lost_c += need * (price - ucost)
        # holding + reorder
        onhand = sum(q for q, _ in lots)
        hold_c += onhand * ucost * HOLD_RATE
        pos = onhand + sum(q for _, q in pipeline[name])
        if pos <= rop:
            pipeline[name].append((d + LEAD, oq))
            orders += 1; ord_c += ORDER_COST
        if name in TRACK:
            series[name].append(onhand)

service = 100 * fulfilled / max(1, demand_tot)
total_cost = hold_c + lost_c + exp_c + ord_c

print("=" * 58)
print(" RETAIL INVENTORY MANAGEMENT SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Demand (units)      : {demand_tot}")
print(f" Service level       : {service:5.1f} %")
print(f" Orders placed       : {orders}")
print(f" Units expired       : {waste_units}")
print(f" Revenue             : Rs. {revenue:,.0f}")
print(f" Holding cost        : Rs. {hold_c:,.0f}")
print(f" Lost-sales margin   : Rs. {lost_c:,.0f}")
print(f" Expiry loss         : Rs. {exp_c:,.0f}")
print(f" Ordering cost       : Rs. {ord_c:,.0f}")
print(f" Total inventory cost: Rs. {total_cost:,.0f}")

save_results({
    "Customer demand (units, 90 days)": demand_tot,
    "Service level (%)": f"{service:.1f}",
    "Purchase orders placed": orders,
    "Units lost to expiry": waste_units,
    "Revenue (Rs.)": f"{revenue:,.0f}",
    "Total inventory cost (Rs.)": f"{total_cost:,.0f}",
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    for t in TRACK:
        plt.plot(range(DAYS), series[t], label=t, lw=1.1)
    plt.xlabel("Day"); plt.ylabel("Units on hand"); plt.legend()
    plt.title("On-Hand Inventory of Key SKUs")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.bar(["Holding", "Lost sales", "Expiry", "Ordering"],
            [hold_c, lost_c, exp_c, ord_c], color="#e67e22")
    plt.ylabel("Cost (Rs.)"); plt.title("Inventory Cost Break-up (90 days)")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
