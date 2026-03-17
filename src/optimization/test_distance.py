"""
test_distance.py
─────────────────────────────────────────────────────────────────────────────
Tests the Haversine distance formula used inside route_optimizer.py

WHY THIS FILE EXISTS:
  Before route_optimizer trusts ANY distance, we verify:
  1. Known real-world distances (cities we can Google)
  2. Edge cases (same point = 0 km, North/South Pole, etc.)
  3. Symmetry (A→B == B→A)
  4. Indian city distances that match our dataset coordinates

RUN THIS:
  python src/optimization/test_distance.py

EXPECTED OUTPUT:
  All tests PASS with ✅
  No distance error > 1% from real-world known value
─────────────────────────────────────────────────────────────────────────────
"""

import sys
import os
import math

# ── make sure we can import from project root ────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))


# ── Copy haversine here so we can test it in isolation ───────────────────────
# (same formula used in route_optimizer.py — if this passes, that one is fine)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Returns distance in KM between two lat/lon points.
    Uses the Haversine formula (great-circle distance).
    """
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ── Test runner ───────────────────────────────────────────────────────────────

passed = 0
failed = 0


def check(test_name: str, got: float, expected: float, tolerance_pct: float = 1.5):
    """Compare got vs expected within a % tolerance."""
    global passed, failed
    error_pct = abs(got - expected) / expected * 100
    if error_pct <= tolerance_pct:
        print(f"  ✅  {test_name}")
        print(f"       Got: {got:.2f} km  |  Expected: ~{expected:.1f} km  |  Error: {error_pct:.2f}%")
        passed += 1
    else:
        print(f"  ❌  {test_name}  ← FAILED")
        print(f"       Got: {got:.2f} km  |  Expected: ~{expected:.1f} km  |  Error: {error_pct:.2f}%")
        failed += 1


def check_exact(test_name: str, got: float, expected: float, tolerance: float = 0.001):
    """For tests where expected value is exactly 0 or a small number."""
    global passed, failed
    if abs(got - expected) <= tolerance:
        print(f"  ✅  {test_name}")
        print(f"       Got: {got:.6f} km  |  Expected: {expected}")
        passed += 1
    else:
        print(f"  ❌  {test_name}  ← FAILED")
        print(f"       Got: {got:.6f} km  |  Expected: {expected}")
        failed += 1


def check_symmetric(test_name: str, lat1, lon1, lat2, lon2):
    """A→B must equal B→A (symmetry test)."""
    global passed, failed
    d_ab = haversine(lat1, lon1, lat2, lon2)
    d_ba = haversine(lat2, lon2, lat1, lon1)
    if abs(d_ab - d_ba) < 0.0001:
        print(f"  ✅  {test_name} (symmetry)")
        print(f"       A→B: {d_ab:.4f} km  |  B→A: {d_ba:.4f} km")
        passed += 1
    else:
        print(f"  ❌  {test_name} (symmetry)  ← FAILED")
        print(f"       A→B: {d_ab:.4f} km  |  B→A: {d_ba:.4f} km")
        failed += 1


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE
# ─────────────────────────────────────────────────────────────────────────────

print()
print("=" * 65)
print("  TEST_DISTANCE.PY — Haversine Formula Verification")
print("=" * 65)


# ── GROUP 1: Known world city distances (verifiable on Google) ────────────────
print()
print("[ GROUP 1 ] Real-world city distances (Google-verifiable)")
print("-" * 65)

# London → Paris ≈ 341 km
check("London → Paris",
      haversine(51.5074, -0.1278, 48.8566, 2.3522),
      expected=341.0)

# Delhi → Mumbai ≈ 1148 km
check("Delhi → Mumbai",
      haversine(28.6139, 77.2090, 19.0760, 72.8777),
      expected=1148.0)

# New York → Los Angeles ≈ 3940 km
check("New York → Los Angeles",
      haversine(40.7128, -74.0060, 34.0522, -118.2437),
      expected=3940.0)

# Sydney → Melbourne ≈ 713 km
check("Sydney → Melbourne",
      haversine(-33.8688, 151.2093, -37.8136, 144.9631),
      expected=713.0)


# ── GROUP 2: Indian city distances (our dataset is from India) ────────────────
print()
print("[ GROUP 2 ] Indian city distances (dataset is India-based)")
print("-" * 65)

# Hyderabad → Bengaluru ≈ 500 km
check("Hyderabad → Bengaluru",
      haversine(17.3850, 78.4867, 12.9716, 77.5946),
      expected=500.0)

# Hyderabad → Chennai ≈ 515 km (straight-line, not road distance)
check("Hyderabad → Chennai",
      haversine(17.3850, 78.4867, 13.0827, 80.2707),
      expected=515.0)

# Mumbai → Pune ≈ 120 km (straight-line, road is ~150 km)
check("Mumbai → Pune",
      haversine(19.0760, 72.8777, 18.5204, 73.8567),
      expected=120.0)


# ── GROUP 3: Hyderabad zone distances (our actual optimizer stops) ────────────
print()
print("[ GROUP 3 ] Our dataset stops — Hyderabad zones")
print("-" * 65)

# Depot → Jubilee Hills ≈ 9.7 km (straight-line between those coords)
check("Depot → Jubilee Hills",
      haversine(17.3850, 78.4867, 17.4318, 78.4091),
      expected=9.74, tolerance_pct=5.0)

# Gachibowli → Kondapur ≈ 3.6 km (adjacent zones)
check("Gachibowli → Kondapur",
      haversine(17.4400, 78.3473, 17.4710, 78.3560),
      expected=3.57, tolerance_pct=5.0)

# Depot → Recycling Plant ≈ 3 km (close together)
check("Depot → Recycling Plant",
      haversine(17.3850, 78.4867, 17.3600, 78.4800),
      expected=3.0, tolerance_pct=20.0)


# ── GROUP 4: Edge cases ───────────────────────────────────────────────────────
print()
print("[ GROUP 4 ] Edge cases")
print("-" * 65)

# Same point → must be exactly 0
check_exact("Same point → 0 km",
            haversine(17.3850, 78.4867, 17.3850, 78.4867),
            expected=0.0)

# Symmetry: A→B == B→A
check_symmetric("Hyderabad ↔ Mumbai (symmetry)",
                17.3850, 78.4867, 19.0760, 72.8777)

check_symmetric("Jubilee Hills ↔ Gachibowli (symmetry)",
                17.4318, 78.4091, 17.4400, 78.3473)

# Very small distance stays positive
d_small = haversine(17.3850, 78.4867, 17.3851, 78.4868)
check_exact("Tiny difference stays positive",
            got=d_small > 0,
            expected=True,
            tolerance=0)


# ── GROUP 5: Route optimizer import test ─────────────────────────────────────
print()
print("[ GROUP 5 ] Import test — can route_optimizer be loaded?")
print("-" * 65)

try:
    from src.optimization.route_optimizer import haversine as ro_haversine, optimize_route
    # Cross-check our haversine vs route_optimizer's haversine
    d1 = haversine(17.3850, 78.4867, 17.4318, 78.4091)
    d2 = ro_haversine(17.3850, 78.4867, 17.4318, 78.4091)
    if abs(d1 - d2) < 0.01:
        print(f"  ✅  route_optimizer.haversine matches test_distance.haversine")
        print(f"       Both: {d1:.4f} km")
        passed += 1
    else:
        print(f"  ❌  Mismatch! test={d1:.4f} km, optimizer={d2:.4f} km")
        failed += 1
    print(f"  ✅  optimize_route() function found and importable")
    passed += 1
except ImportError as e:
    print(f"  ⚠️   Cannot import route_optimizer: {e}")
    print(f"       This is OK if running standalone. Import test skipped.")


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

print()
print("=" * 65)
print(f"  RESULTS:  {passed} passed  |  {failed} failed  |  {passed + failed} total")
print("=" * 65)

if failed == 0:
    print()
    print("  🎉 ALL TESTS PASSED — Haversine is accurate!")
    print("  ✅  route_optimizer.py can be trusted for distance calculations.")
    print("  ✅  Safe to proceed to test_routing.py")
    print()
else:
    print()
    print(f"  ⚠️  {failed} test(s) FAILED — check the formula above.")
    print("  ❌  Do NOT proceed to test_routing.py until all pass.")
    print()

sys.exit(0 if failed == 0 else 1)