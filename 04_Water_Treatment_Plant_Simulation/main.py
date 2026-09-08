"""
WATER TREATMENT PLANT OPERATIONS SIMULATION
Single-file time-stepped simulation of a municipal water treatment
train: intake -> coagulation -> sedimentation -> filtration ->
chlorination, with turbidity-driven chemical dosing and a clear-water
tank serving a varying town demand.
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import math, random, os

random.seed(3)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
MINUTES     = 720                 # 12-hour operating window
INFLOW      = 2000.0              # litres per minute raw intake
TANK_CAP    = 600000.0            # clear-water tank capacity (L)
START_LEVEL = 0.55                # tank starts 55 % full
MAX_DOSE    = 45.0                # coagulant pump limit (mg/L)
NTU_LIMIT   = 1.0                 # potable turbidity limit

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

def demand(m):                    # town demand profile (L/min)
    return 1900 + 500 * math.sin(2 * math.pi * (m - 200) / 720)

level = TANK_CAP * START_LEVEL
coag_kg = cl_kg = 0.0
compliant = 0
tin_log, tout_log, lvl_log = [], [], []
spike = 0.0

for m in range(MINUTES):
    # ---- raw water turbidity (NTU) with random storm spikes ----
    spike = max(0.0, spike - 0.8)
    if random.random() < 0.01:
        spike += random.uniform(60, 150)
    turb_in = max(5.0, 90 + 45 * math.sin(2*math.pi*m/480)
                  + random.gauss(0, 6) + spike)

    # ---- coagulation: dose proportional to turbidity ----------
    needed = 4 + 0.16 * turb_in
    dose = min(MAX_DOSE, needed)
    adequacy = dose / needed
    coag_kg += dose * INFLOW / 1e6            # mg/L * L -> kg

    # ---- sedimentation + rapid sand filtration ----------------
    after_sed  = turb_in * (1 - 0.72 * adequacy)
    turb_out   = after_sed * 0.18

    # ---- chlorination to hold residual ------------------------
    cl_dose = 0.8 + 0.3 + 0.004 * turb_out
    cl_kg  += cl_dose * INFLOW / 1e6

    if turb_out < NTU_LIMIT:
        compliant += 1

    # ---- clear water tank balance ------------------------------
    out = demand(m)
    inflow_eff = INFLOW if level < 0.97 * TANK_CAP else out
    level = max(0.0, min(TANK_CAP, level + inflow_eff - out))

    tin_log.append(turb_in); tout_log.append(turb_out)
    lvl_log.append(100 * level / TANK_CAP)

avg_out = sum(tout_log) / len(tout_log)
comp_pc = 100 * compliant / MINUTES
min_lvl = min(lvl_log)
ml_prod = INFLOW * MINUTES / 1e6

print("=" * 58)
print(" WATER TREATMENT PLANT SIMULATION -- SUMMARY")
print("=" * 58)
print(f" Water produced           : {ml_prod:5.2f} ML")
print(f" Avg outlet turbidity     : {avg_out:5.3f} NTU")
print(f" Compliance (< 1 NTU)     : {comp_pc:5.1f} % of minutes")
print(f" Coagulant used           : {coag_kg:5.1f} kg")
print(f" Chlorine used            : {cl_kg:5.1f} kg")
print(f" Minimum tank level       : {min_lvl:5.1f} %")

save_results({
    "Water produced (ML)": f"{ml_prod:.2f}",
    "Average outlet turbidity (NTU)": f"{avg_out:.3f}",
    "Compliance below 1 NTU (%)": f"{comp_pc:.1f}",
    "Coagulant consumed (kg)": f"{coag_kg:.1f}",
    "Chlorine consumed (kg)": f"{cl_kg:.1f}",
    "Minimum clear-water tank level (%)": f"{min_lvl:.1f}",
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = [m/60 for m in range(MINUTES)]
    plt.figure(figsize=(7, 4))
    plt.plot(x, tin_log, label="Raw water", lw=0.9)
    plt.plot(x, tout_log, label="Treated water", lw=0.9)
    plt.yscale("log"); plt.axhline(1.0, color="red", ls="--", lw=0.8,
                                   label="1 NTU limit")
    plt.xlabel("Time (hours)"); plt.ylabel("Turbidity (NTU, log)")
    plt.title("Turbidity Before and After Treatment"); plt.legend()
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.plot(x, lvl_log, color="#2c3e50")
    plt.xlabel("Time (hours)"); plt.ylabel("Tank level (%)")
    plt.title("Clear-Water Tank Level"); plt.ylim(0, 100)
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
