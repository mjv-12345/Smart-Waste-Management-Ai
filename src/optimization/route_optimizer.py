# ================================================================
#  FILE 5 of 7  —  src/optimization/route_optimizer.py
#
#  ROLE IN THE CHAIN:
#  ┌─────────────────────────────────────────────────────┐
#  │  travel_time_model.pkl  (saved by FILE 4)           │
#  │       │  joblib.load()                              │
#  │       ▼                                             │
#  │  route_optimizer.py  ◄── YOU ARE HERE               │
#  │       │                                             │
#  │       ▼  (imported by)                              │
#  │  decision_logic.py → backend/main.py → frontend     │
#  └─────────────────────────────────────────────────────┘
#
#  WHAT THIS FILE DOES — 4 STAGE PIPELINE:
#
#  STAGE 1 — ML SCORING
#  ┌─────────────────────────────────────────┐
#  │  For every pair of stops (A→B, A→C ...) │
#  │  ask travel_time_model:                 │
#  │  "How many minutes does A→B take?"      │
#  │  Result = cost matrix (NxN grid)        │
#  └─────────────────────────────────────────┘
#           │
#           ▼
#  STAGE 2 — GREEDY NEAREST NEIGHBOUR
#  ┌─────────────────────────────────────────┐
#  │  Start at depot                         │
#  │  Always go to the NEAREST unvisited     │
#  │  stop next                              │
#  │  Builds a complete but rough route      │
#  └─────────────────────────────────────────┘
#           │
#           ▼
#  STAGE 3 — 2-OPT IMPROVEMENT
#  ┌─────────────────────────────────────────┐
#  │  Take the greedy route                  │
#  │  Try reversing every pair of segments   │
#  │  If reversal is shorter → keep it       │
#  │  Repeat until no improvement found      │
#  │  Result = optimized route               │
#  └─────────────────────────────────────────┘
#           │
#           ▼
#  STAGE 4 — RETURN RESULTS
#  ┌─────────────────────────────────────────┐
#  │  Ordered stop list                      │
#  │  Total distance (km)                    │
#  │  Total time (minutes)                   │
#  │  Distance saved vs greedy (%)           │
#  └─────────────────────────────────────────┘
#
#  INPUT:  list of stops with lat/lon + vehicle details
#  OUTPUT: optimized ordered stop sequence + savings
# ================================================================

import os
import sys
import numpy as np
import joblib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)

# Paths to the model and scaler saved by FILE 4
MODEL_PATH  = os.path.join(BASE_DIR, "backend", "trained_models", "travel_time_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "data",    "processed",      "scaler_route.pkl")


# ================================================================
#  LOAD MODEL + SCALER
#  Called once when this module is imported
#  So the model is ready in memory for every request
# ================================================================
def load_model():
    """
    Loads travel_time_model.pkl saved by FILE 4.
    Returns (model, scaler) or (None, None) if not trained yet.
    """
    if not os.path.exists(MODEL_PATH):
        print(f"  ⚠️  Model not found at {MODEL_PATH}")
        print(f"      Run: python src/models/train_travel_time_model.py")
        return None, None

    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler


# ================================================================
#  HAVERSINE DISTANCE
#  Calculates real-world distance (km) between two GPS points
#  Used to build the base cost matrix before ML scoring
#
#  Formula:
#  a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
#  distance = 2R × arcsin(√a)   where R = 6371 km
# ================================================================
def haversine(lat1, lon1, lat2, lon2):
    R    = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a    = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))


# ================================================================
#  STAGE 1 — BUILD COST MATRIX
#
#  For N stops we create an N×N matrix where
#  matrix[i][j] = predicted travel time from stop i to stop j
#
#  Each cell uses the ML model with these features:
#  [distance_km, vehicle_capacity, current_load,
#   fuel_consumption, traffic, road_type, road_condition,
#   one_way, toll, lat, lon]
#
#  If model not available → falls back to haversine distance
# ================================================================
def build_cost_matrix(stops, vehicle, model, scaler):
    """
    stops   = list of dicts with keys:
              lat, lon, traffic, road_type, road_condition,
              one_way, toll
    vehicle = dict with keys:
              capacity_kg, current_load_kg, fuel_km_per_l

    Returns NxN numpy matrix of predicted travel times (minutes)
    """
    n      = len(stops)
    matrix = np.zeros((n, n))

    # Encode traffic/road values to numbers
    # Must match exactly what preprocess.py used
    traffic_map   = {"High": 0, "Low": 1, "Medium": 2}
    road_type_map = {"Highway": 0, "Main_Road": 1, "Residential": 2}
    road_cond_map = {"Average": 0, "Good": 1, "Poor": 2}

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0
                continue

            # Real distance between stop i and stop j
            dist = haversine(
                stops[i]["lat"], stops[i]["lon"],
                stops[j]["lat"], stops[j]["lon"]
            )

            if model is not None:
                # Build feature vector matching ROUTE_FEATURES order:
                # Distance_km, Vehicle_Capacity_kg, Current_Load_kg,
                # Fuel_Consumption_km_per_l, Traffic_Congestion_Level,
                # Road_Type, Road_Condition, One_Way_Flag, Toll_Road,
                # Vehicle_Location_Lat, Vehicle_Location_Long
                features = np.array([[
                    dist,
                    vehicle.get("capacity_kg",    5000),
                    vehicle.get("current_load_kg", 2000),
                    vehicle.get("fuel_km_per_l",   5.0),
                    traffic_map.get(stops[j].get("traffic", "Medium"), 2),
                    road_type_map.get(stops[j].get("road_type", "Main_Road"), 1),
                    road_cond_map.get(stops[j].get("road_condition", "Average"), 0),
                    stops[j].get("one_way", 0),
                    stops[j].get("toll",    0),
                    stops[i]["lat"],
                    stops[i]["lon"],
                ]])

                # Scale with the same scaler used in training
                features_scaled  = scaler.transform(features)
                predicted_time   = model.predict(features_scaled)[0]

                # Use predicted time as the cost
                # (higher time = more expensive edge)
                matrix[i][j] = max(predicted_time, 0)
            else:
                # Fallback: use raw distance as cost
                matrix[i][j] = dist

    return matrix


# ================================================================
#  STAGE 2 — GREEDY NEAREST NEIGHBOUR
#
#  Simple but fast route construction:
#  1. Start at depot (index 0)
#  2. Find the nearest unvisited stop
#  3. Go there
#  4. Repeat until all stops visited
#  5. Return to depot
#
#  This gives a complete route but NOT the shortest one.
#  It is then improved by 2-opt in Stage 3.
# ================================================================
def greedy_route(matrix):
    n       = len(matrix)
    visited = [False] * n
    route   = [0]           # start at depot (index 0)
    visited[0] = True

    for _ in range(n - 1):
        current   = route[-1]
        best_next = -1
        best_cost = float("inf")

        for j in range(n):
            if not visited[j] and matrix[current][j] < best_cost:
                best_cost = matrix[current][j]
                best_next = j

        route.append(best_next)
        visited[best_next] = True

    route.append(0)     # return to depot
    return route


# ================================================================
#  STAGE 3 — 2-OPT IMPROVEMENT
#
#  How 2-opt works:
#  Given route: [0, A, B, C, D, E, 0]
#
#  Try reversing every sub-segment:
#  Original:  0 → A → B → C → D → E → 0
#  Try swap:  0 → A → C → B → D → E → 0  (reversed B,C)
#
#  If the new route is shorter → keep the swap
#  Repeat until no swap improves the route
#
#  WHY THIS WORKS:
#  Greedy routes often cross over themselves.
#  2-opt untangles these crossings.
#  Each iteration can only improve or stay the same.
# ================================================================
def total_cost(route, matrix):
    """Calculates total cost of a route using the cost matrix."""
    return sum(matrix[route[i]][route[i+1]] for i in range(len(route)-1))


def two_opt(route, matrix):
    """
    Improves a route using 2-opt local search.
    Keeps swapping until no improvement found.
    Returns improved route.
    """
    best      = route[:]
    best_cost = total_cost(best, matrix)
    improved  = True

    while improved:
        improved = False
        # Try every pair of edges (i, j)
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                # Reverse the segment between i and j
                new_route = best[:i] + best[i:j+1][::-1] + best[j+1:]
                new_cost  = total_cost(new_route, matrix)

                if new_cost < best_cost - 1e-6:
                    best      = new_route
                    best_cost = new_cost
                    improved  = True   # found improvement → keep going

    return best


# ================================================================
#  STAGE 4 — MAIN OPTIMIZE FUNCTION
#  Called by decision_logic.py when API receives /optimize request
#
#  INPUT:
#  stops = [
#    {"name": "Depot",  "lat": 17.38, "lon": 78.48,
#     "traffic": "Low", "road_type": "Highway",
#     "road_condition": "Good", "one_way": 0, "toll": 0},
#    {"name": "Zone A", "lat": 17.43, "lon": 78.41,
#     "traffic": "High", ...},
#    ...
#  ]
#  vehicle = {
#    "capacity_kg": 5000,
#    "current_load_kg": 0,
#    "fuel_km_per_l": 5.0
#  }
#
#  OUTPUT:
#  {
#    "optimized_route"   : [ordered stop names],
#    "total_distance_km" : 24.3,
#    "total_time_min"    : 48.6,
#    "greedy_distance_km": 31.7,
#    "saved_percent"     : 23.3,
#    "num_stops"         : 6
#  }
# ================================================================
def optimize_route(stops, vehicle):
    print(f"\n[OPTIMIZER] Starting route optimization")
    print(f"            Stops    : {len(stops)}")
    print(f"            Vehicle  : {vehicle}")

    # Load model from FILE 4
    model, scaler = load_model()

    # STAGE 1: Build cost matrix
    print(f"\n  [Stage 1] Building {len(stops)}×{len(stops)} cost matrix ...")
    matrix = build_cost_matrix(stops, vehicle, model, scaler)

    # STAGE 2: Greedy route
    print(f"  [Stage 2] Running greedy nearest neighbour ...")
    greedy  = greedy_route(matrix)
    g_cost  = total_cost(greedy, matrix)

    # Calculate real-world greedy distance using haversine
    g_dist = sum(
        haversine(stops[greedy[i]]["lat"], stops[greedy[i]]["lon"],
                  stops[greedy[i+1]]["lat"], stops[greedy[i+1]]["lon"])
        for i in range(len(greedy)-1)
    )
    print(f"            Greedy route cost : {g_cost:.2f}")
    print(f"            Greedy distance   : {g_dist:.2f} km")

    # STAGE 3: 2-opt improvement
    print(f"  [Stage 3] Running 2-opt improvement ...")
    optimized = two_opt(greedy, matrix)
    o_cost    = total_cost(optimized, matrix)

    # Calculate real-world optimized distance
    o_dist = sum(
        haversine(stops[optimized[i]]["lat"], stops[optimized[i]]["lon"],
                  stops[optimized[i+1]]["lat"], stops[optimized[i+1]]["lon"])
        for i in range(len(optimized)-1)
    )

    # Calculate savings
    saved_pct = ((g_dist - o_dist) / g_dist * 100) if g_dist > 0 else 0

    # Estimated time at 30 km/h average urban speed
    total_time = (o_dist / 30) * 60

    print(f"            Optimized cost    : {o_cost:.2f}")
    print(f"            Optimized distance: {o_dist:.2f} km")
    print(f"            Saved             : {saved_pct:.1f}%")

    # STAGE 4: Build result
    ordered_stops = [stops[i]["name"] for i in optimized]

    # Build step-by-step directions
    directions = []
    for i in range(len(optimized) - 1):
        a    = stops[optimized[i]]
        b    = stops[optimized[i+1]]
        dist = haversine(a["lat"], a["lon"], b["lat"], b["lon"])
        directions.append({
            "step"       : i + 1,
            "from"       : a["name"],
            "to"         : b["name"],
            "distance_km": round(dist, 2),
            "time_min"   : round((dist / 30) * 60, 1)
        })

    result = {
    "optimized_route"    : ordered_stops,
    "ordered_stops"      : [stops[i] for i in optimized],
    "directions"         : directions,
    "total_distance_km"  : round(o_dist, 2),
    "total_time_min"     : round(total_time, 1),
    "greedy_distance_km" : round(g_dist, 2),
    "saved_km"           : round(g_dist - o_dist, 2),
    "saved_percent"      : round(saved_pct, 1),
    "improvement_percent": round(saved_pct, 1),
    "greedy_cost"        : round(g_cost, 2),
    "total_cost_score"   : round(o_cost, 2),
    "num_stops"          : len(stops),
    "algorithm"          : "Greedy + 2-opt"
}

    print(f"\n[OPTIMIZER] ✅ Done")
    print(f"            Route : {' → '.join(ordered_stops)}")
    print(f"            Total : {o_dist:.2f} km  |  {total_time:.0f} min")
    print(f"            Saved : {saved_pct:.1f}% vs greedy\n")

    return result


# ================================================================
#  TEST THIS FILE DIRECTLY:
#  python src/optimization/route_optimizer.py
# ================================================================
if __name__ == "__main__":
    # Sample test stops (Hyderabad zones)
    test_stops = [
        {"name": "Depot",       "lat": 17.385, "lon": 78.487,
         "traffic": "Low",    "road_type": "Highway",     "road_condition": "Good",    "one_way": 0, "toll": 0},
        {"name": "Zone A",      "lat": 17.431, "lon": 78.409,
         "traffic": "High",   "road_type": "Main_Road",   "road_condition": "Average", "one_way": 0, "toll": 0},
        {"name": "Zone B",      "lat": 17.415, "lon": 78.441,
         "traffic": "Medium", "road_type": "Main_Road",   "road_condition": "Good",    "one_way": 1, "toll": 0},
        {"name": "Zone C",      "lat": 17.449, "lon": 78.390,
         "traffic": "High",   "road_type": "Highway",     "road_condition": "Good",    "one_way": 0, "toll": 1},
        {"name": "Zone D",      "lat": 17.440, "lon": 78.347,
         "traffic": "Medium", "road_type": "Highway",     "road_condition": "Average", "one_way": 0, "toll": 0},
        {"name": "Zone E",      "lat": 17.471, "lon": 78.356,
         "traffic": "Low",    "road_type": "Residential", "road_condition": "Poor",    "one_way": 0, "toll": 0},
        {"name": "Recycle Plant","lat": 17.360, "lon": 78.480,
         "traffic": "Low",    "road_type": "Highway",     "road_condition": "Good",    "one_way": 0, "toll": 0},
    ]

    test_vehicle = {
        "capacity_kg"    : 5000,
        "current_load_kg": 0,
        "fuel_km_per_l"  : 5.0
    }

    result = optimize_route(test_stops, test_vehicle)

    print("="*55)
    print("  OPTIMIZATION RESULT")
    print("="*55)
    print(f"  Route    : {' → '.join(result['optimized_route'])}")
    print(f"  Distance : {result['total_distance_km']} km")
    print(f"  Time     : {result['total_time_min']} min")
    print(f"  Saved    : {result['saved_percent']}% vs greedy")
    print()
    print("  Step-by-step directions:")
    for d in result["directions"]:
        print(f"  {d['step']}. {d['from']:15s} → {d['to']:15s}  {d['distance_km']} km  {d['time_min']} min")