"""
debug_solver.py
─────────────────────────────────────────────────────────────────────────────
Step-by-step debugger for the route optimizer.

WHY THIS FILE EXISTS:
  test_routing.py confirms the algorithm WORKS.
  THIS file shows you exactly WHAT it's doing at each step —
  so when something looks wrong in the frontend, you can trace it here.

  Shows:
    1. Full distance matrix (every stop to every other stop)
    2. Greedy step-by-step decisions (which stop it picked and why)
    3. 2-opt swap log (every improvement it found)
    4. Before vs After comparison with route diagram
    5. Per-edge breakdown (how long each segment is)

RUN THIS:
  cd SMART-WA  (your project root)
  python src/optimization/debug_solver.py

EXPECTED OUTPUT:
  Full printed trace with no errors.
  Use this when the frontend shows a weird route.
─────────────────────────────────────────────────────────────────────────────
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))


# ─────────────────────────────────────────────────────────────────────────────
# Core helpers (same as route_optimizer.py)
# ─────────────────────────────────────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def route_cost(route, matrix):
    return sum(matrix[route[k]][route[k+1]] for k in range(len(route)-1))


# ─────────────────────────────────────────────────────────────────────────────
# DEBUG STEP 1: Distance Matrix
# ─────────────────────────────────────────────────────────────────────────────

def debug_distance_matrix(stops):
    n = len(stops)
    matrix = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = haversine(
                    stops[i]["lat"], stops[i]["lon"],
                    stops[j]["lat"], stops[j]["lon"]
                )

    print()
    print("=" * 65)
    print("  STEP 1 -- DISTANCE MATRIX (km, straight-line Haversine)")
    print("=" * 65)

    labels = [s["id"][:6].center(8) for s in stops]
    print("         " + "".join(labels))
    print("         " + "-" * (8 * n))

    for i, stop in enumerate(stops):
        row_label = stop["id"][:6].ljust(8)
        row_vals  = ""
        for j in range(n):
            if i == j:
                row_vals += "   --   "
            else:
                row_vals += f"{matrix[i][j]:6.2f}  "
        print(f"  {row_label} {row_vals}")

    print()
    print("  Nearest neighbour from each stop:")
    for i, stop in enumerate(stops):
        dists = [(matrix[i][j], j) for j in range(n) if j != i]
        dists.sort()
        nearest_idx  = dists[0][1]
        nearest_dist = dists[0][0]
        print(f"    {stop['id'][:8]:<10} -> {stops[nearest_idx]['id']:<12}  ({nearest_dist:.2f} km)")

    return matrix


# ─────────────────────────────────────────────────────────────────────────────
# DEBUG STEP 2: Greedy step-by-step
# ─────────────────────────────────────────────────────────────────────────────

def debug_greedy(stops, matrix, depot=0):
    n       = len(stops)
    visited = [False] * n
    route   = [depot]
    visited[depot] = True
    total   = 0.0

    print()
    print("=" * 65)
    print("  STEP 2 -- GREEDY NEAREST-NEIGHBOUR (step by step)")
    print("=" * 65)
    print(f"  Start at: {stops[depot]['name']} (index {depot})")
    print()

    step = 1
    while len(route) < n:
        cur     = route[-1]
        options = sorted(
            [(matrix[cur][j], j) for j in range(n) if not visited[j]]
        )
        best_dist, best_next = options[0]

        print(f"  Step {step:2d}  From: {stops[cur]['name']:<25}")
        for dist, idx in options:
            chosen = " <- CHOSEN" if idx == best_next else ""
            print(f"           ->  {stops[idx]['name']:<25}  {dist:6.2f} km{chosen}")

        route.append(best_next)
        visited[best_next] = True
        total += best_dist
        step  += 1
        print()

    return_dist = matrix[route[-1]][depot]
    route.append(depot)
    total += return_dist
    print(f"  Step {step:2d}  Return to depot: {return_dist:.2f} km")
    print()
    print(f"  Greedy route: {' -> '.join(stops[i]['id'] for i in route)}")
    print(f"  Greedy total: {total:.2f} km")

    return route, total


# ─────────────────────────────────────────────────────────────────────────────
# DEBUG STEP 3: 2-opt with swap log
# ─────────────────────────────────────────────────────────────────────────────

def debug_two_opt(route, matrix, stops, max_iter=500):
    print()
    print("=" * 65)
    print("  STEP 3 -- 2-OPT LOCAL SEARCH (swap log)")
    print("=" * 65)
    print(f"  Starting cost: {route_cost(route, matrix):.4f} km")
    print()

    best       = route[:]
    best_cost  = route_cost(best, matrix)
    improved   = True
    iterations = 0
    swap_count = 0

    while improved and iterations < max_iter:
        improved   = False
        iterations += 1

        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                new_route = best[:i] + best[i:j+1][::-1] + best[j+1:]
                new_cost  = route_cost(new_route, matrix)

                if new_cost < best_cost - 1e-6:
                    gain       = best_cost - new_cost
                    swap_count += 1
                    print(f"  Swap #{swap_count:2d}  iter={iterations}  i={i} j={j}  "
                          f"cost {best_cost:.4f} -> {new_cost:.4f}  (saved {gain:.4f} km)")
                    print(f"    Before: {' -> '.join(stops[x]['id'] for x in best)}")
                    print(f"    After:  {' -> '.join(stops[x]['id'] for x in new_route)}")
                    print()
                    best      = new_route
                    best_cost = new_cost
                    improved  = True

    if swap_count == 0:
        print("  No improving swaps found -- greedy route was already optimal.")
    else:
        print(f"  2-opt finished: {swap_count} swap(s) across {iterations} iteration(s)")

    print()
    print(f"  Final route: {' -> '.join(stops[i]['id'] for i in best)}")
    print(f"  Final cost:  {best_cost:.4f} km")

    return best, best_cost


# ─────────────────────────────────────────────────────────────────────────────
# DEBUG STEP 4: Per-edge breakdown
# ─────────────────────────────────────────────────────────────────────────────

def debug_edge_breakdown(route, stops, matrix):
    print()
    print("=" * 65)
    print("  STEP 4 -- PER-EDGE BREAKDOWN")
    print("=" * 65)
    print(f"  {'#':>3}  {'From':<22}  {'To':<22}  {'km':>7}  {'min @ 30':>10}")
    print(f"  {'---'}  {'----------------------'}  {'----------------------'}  {'-------'}  {'----------'}")

    total_km  = 0.0
    total_min = 0.0

    for k in range(len(route) - 1):
        a    = stops[route[k]]
        b    = stops[route[k+1]]
        dist = matrix[route[k]][route[k+1]]
        mins = (dist / 30) * 60
        total_km  += dist
        total_min += mins
        print(f"  {k+1:>3}  {a['name']:<22}  {b['name']:<22}  {dist:>7.2f}  {mins:>8.1f} min")

    print(f"  {'---'}  {'----------------------'}  {'----------------------'}  {'-------'}  {'----------'}")
    print(f"  {'TOT':>3}  {'':22}  {'':22}  {total_km:>7.2f}  {total_min:>8.1f} min")


# ─────────────────────────────────────────────────────────────────────────────
# DEBUG STEP 5: Before vs After comparison + ASCII map
# ─────────────────────────────────────────────────────────────────────────────

def debug_comparison(greedy_route, opt_route, greedy_cost, opt_cost, stops):
    improvement = ((greedy_cost - opt_cost) / (greedy_cost + 1e-9)) * 100
    saved_km    = greedy_cost - opt_cost
    saved_min   = (saved_km / 30) * 60
    fuel_saved  = saved_km / 5.0

    print()
    print("=" * 65)
    print("  STEP 5 -- BEFORE vs AFTER SUMMARY")
    print("=" * 65)
    print()
    print(f"  {'Metric':<26}  {'Greedy':>10}  {'2-Opt':>10}  {'Saved':>8}")
    print(f"  {'─'*26}  {'─'*10}  {'─'*10}  {'─'*8}")
    g_min = (greedy_cost / 30) * 60
    o_min = (opt_cost   / 30) * 60
    print(f"  {'Total Distance (km)':<26}  {greedy_cost:>10.2f}  {opt_cost:>10.2f}  {saved_km:>+8.2f}")
    print(f"  {'Travel Time (min)':<26}  {g_min:>10.1f}  {o_min:>10.1f}  {saved_min:>+8.1f}")
    print(f"  {'Fuel Used (L at 5km/L)':<26}  {greedy_cost/5:>10.2f}  {opt_cost/5:>10.2f}  {fuel_saved:>+8.2f}")
    print(f"  {'Improvement':<26}  {'':>10}  {improvement:>9.1f}%")
    print()
    print(f"  Greedy: {' -> '.join(stops[i]['id'] for i in greedy_route)}")
    print(f"  2-opt:  {' -> '.join(stops[i]['id'] for i in opt_route)}")

    # ASCII map
    print()
    print("  ASCII Route Map (2-opt order):")
    print()

    lats = [s["lat"] for s in stops]
    lons = [s["lon"] for s in stops]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    W, H = 52, 13

    def to_xy(lat, lon):
        x = int((lon - min_lon) / (max_lon - min_lon + 1e-9) * (W - 1))
        y = H - 1 - int((lat - min_lat) / (max_lat - min_lat + 1e-9) * (H - 1))
        return max(0, min(W-1, x)), max(0, min(H-1, y))

    grid = [list("." * W) for _ in range(H)]

    # Draw midpoints of each edge
    for k in range(len(opt_route) - 1):
        a  = stops[opt_route[k]]
        b  = stops[opt_route[k+1]]
        ax, ay = to_xy(a["lat"], a["lon"])
        bx, by = to_xy(b["lat"], b["lon"])
        mx, my = (ax+bx)//2, (ay+by)//2
        if grid[my][mx] == ".":
            grid[my][mx] = "-"

    # Place stop labels on top (use index number 0-9)
    for idx, stop in enumerate(stops):
        x, y   = to_xy(stop["lat"], stop["lon"])
        label  = str(idx)
        grid[y][x] = label

    print("  N ^")
    for row in grid:
        print("    |  " + "".join(row))
    print("    +" + "-"*W + "> E")
    print()
    print("  Key:", "  ".join(f"[{i}] {s['name']}" for i, s in enumerate(stops)))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

STOPS = [
    {"id": "DEPOT",  "name": "Municipal Depot",  "lat": 17.3850, "lon": 78.4867},
    {"id": "ZONE-A", "name": "Jubilee Hills",     "lat": 17.4318, "lon": 78.4091},
    {"id": "ZONE-B", "name": "Banjara Hills",     "lat": 17.4156, "lon": 78.4412},
    {"id": "ZONE-C", "name": "Madhapur",          "lat": 17.4490, "lon": 78.3900},
    {"id": "ZONE-D", "name": "Gachibowli",        "lat": 17.4400, "lon": 78.3473},
    {"id": "ZONE-E", "name": "Kondapur",          "lat": 17.4710, "lon": 78.3560},
    {"id": "PLANT",  "name": "Recycling Plant",   "lat": 17.3600, "lon": 78.4800},
]

print()
print("+" + "="*63 + "+")
print("|  DEBUG_SOLVER.PY  --  Route Optimizer Step-by-Step Inspector  |")
print("+" + "="*63 + "+")
print(f"  Stops loaded: {len(STOPS)}")
print(f"  Depot:        {STOPS[0]['name']} ({STOPS[0]['lat']}, {STOPS[0]['lon']})")

matrix          = debug_distance_matrix(STOPS)
greedy, g_cost  = debug_greedy(STOPS, matrix, depot=0)
opt,    o_cost  = debug_two_opt(greedy, matrix, STOPS)

debug_edge_breakdown(opt, STOPS, matrix)
debug_comparison(greedy, opt, g_cost, o_cost, STOPS)

print()
print("=" * 65)
print("  DEBUG COMPLETE -- No errors.")
print("  Paste this output when reporting a route issue.")
print("=" * 65)
print()