"""
COLLEGE EXAM HALL ALLOCATION SIMULATION
Single-file simulation of seat allocation across examination halls so
that no two adjacent students (left / front) write the same paper,
with invigilator assignment and roll-clash verification.
Author : ______________________   Roll No : ______________________
Run    : python main.py
"""
import random, math, os
from collections import deque

random.seed(5)
BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------- CONFIGURATION -----------------------
HALLS = [("Hall A", 10, 8), ("Hall B", 9, 8),
         ("Hall C", 8, 7),  ("Hall D", 7, 6)]        # name, rows, cols
SESSIONS = {
    "Morning Session":   {"BCA": 118, "BCOM": 76},
    "Afternoon Session": {"BBA": 92,  "BSC": 64},
}
SEATS_PER_INVIGILATOR = 30

def save_results(d):
    with open(os.path.join(BASE, "results.txt"), "w") as f:
        for k, v in d.items():
            f.write(f"{k}|{v}\n")

def make_students(courses):
    out = {}
    for c, n in courses.items():
        out[c] = deque(f"R23{c}{i:04d}" for i in range(1, n + 1))
    return out

def allocate(courses):
    """Greedy interleaving allocation with gap seats to avoid
    same-course neighbours. Returns halls' grids + stats."""
    pool = make_students(courses)
    total_students = sum(len(q) for q in pool.values())
    total_seats = sum(r * c for _, r, c in HALLS)
    spare = total_seats - total_students
    grids, gaps_used, placed = [], 0, 0
    for name, rows, cols in HALLS:
        grid = [[None] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                if not any(pool.values()):
                    break
                left  = grid[r][c-1][0] if c > 0 and grid[r][c-1] else None
                front = grid[r-1][c][0] if r > 0 and grid[r-1][c] else None
                # choose the largest course different from neighbours
                order = sorted(pool, key=lambda k: -len(pool[k]))
                pick = next((k for k in order
                             if pool[k] and k != left and k != front), None)
                if pick is None:
                    if spare - gaps_used > 0:      # leave a gap seat
                        gaps_used += 1
                        continue
                    pick = next(k for k in order if pool[k])
                grid[r][c] = (pick, pool[pick].popleft())
                placed += 1
        grids.append((name, grid))
    # count adjacency violations after placement
    violations = 0
    for _, grid in grids:
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if not grid[r][c]:
                    continue
                if c > 0 and grid[r][c-1] and grid[r][c-1][0] == grid[r][c][0]:
                    violations += 1
                if r > 0 and grid[r-1][c] and grid[r-1][c][0] == grid[r][c][0]:
                    violations += 1
    return grids, gaps_used, violations, placed

# ----------------------- RUN ALL SESSIONS --------------------
print("=" * 58)
print(" COLLEGE EXAM HALL ALLOCATION SIMULATION -- SUMMARY")
print("=" * 58)
hall_util = {h[0]: [] for h in HALLS}
tot_inv = tot_viol = tot_gap = 0
course_counts = {}
all_rolls = set(); clash = 0
for sess, courses in SESSIONS.items():
    grids, gaps, viol, placed = allocate(courses)
    inv = 0
    print(f"\n [{sess}]  students placed: {placed},"
          f" gap seats: {gaps}, adjacency violations: {viol}")
    for name, grid in grids:
        occ = sum(1 for row in grid for s in row if s)
        cap = len(grid) * len(grid[0])
        hall_util[name].append(100 * occ / cap)
        inv += math.ceil(occ / SEATS_PER_INVIGILATOR)
        print(f"   {name}: {occ}/{cap} seats "
              f"({100*occ/cap:4.1f}%)")
        for row in grid:
            for s in row:
                if s:
                    if s[1] in all_rolls:
                        clash += 1
                    all_rolls.add(s[1])
    for c, n in courses.items():
        course_counts[c] = n
    tot_inv += inv; tot_viol += viol; tot_gap += gaps
    print(f"   Invigilators required : {inv}")

avg_util = {h: sum(v)/len(v) for h, v in hall_util.items()}
print(f"\n Roll-number clashes detected : {clash}")
print(f" Total invigilators (both)    : {tot_inv}")

save_results({
    "Students allocated (total)": sum(course_counts.values()),
    "Adjacency violations": tot_viol,
    "Gap seats used": tot_gap,
    "Roll-number clashes": clash,
    "Invigilators required (total)": tot_inv,
    "Average hall utilisation (%)": f"{sum(avg_util.values())/len(avg_util):.1f}",
})

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    plt.bar(avg_util.keys(), avg_util.values(), color="#8e44ad")
    plt.ylabel("Average utilisation (%)"); plt.ylim(0, 100)
    plt.title("Examination Hall Seat Utilisation")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart1.png"), dpi=110)
    plt.figure(figsize=(7, 4))
    plt.bar(course_counts.keys(), course_counts.values(), color="#d35400")
    plt.ylabel("Students"); plt.title("Students Allocated per Course")
    plt.tight_layout(); plt.savefig(os.path.join(BASE, "chart2.png"), dpi=110)
    print(" Charts saved: chart1.png, chart2.png")
except Exception as e:
    print(" (matplotlib unavailable, charts skipped)", e)
