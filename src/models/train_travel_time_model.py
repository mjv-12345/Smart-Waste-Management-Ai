# ================================================================
#  FILE 4 of 7  —  src/models/train_travel_time_model.py
#
#  ROLE IN THE CHAIN:
#  ┌─────────────────────────────────────────────────────┐
#  │  preprocess.py                                      │
#  │       │  run_preprocessing() → data["route"]        │
#  │       ▼                                             │
#  │  train_travel_time_model.py  ◄── YOU ARE HERE       │
#  │       │                                             │
#  │       ▼                                             │
#  │  backend/trained_models/travel_time_model.pkl       │
#  │       │                                             │
#  │       ▼  (loaded later by)                          │
#  │  route_optimizer.py  ← FILE 5                       │
#  │       │                                             │
#  │       ▼                                             │
#  │  decision_logic.py → backend/main.py                │
#  └─────────────────────────────────────────────────────┘
#
#  WHAT THIS FILE DOES:
#  1. Calls preprocess.py → gets clean route training data
#  2. Trains 3 ML algorithms on road segment data
#  3. Tests each on 2000 unseen rows
#  4. Picks the best model automatically
#  5. Saves → backend/trained_models/travel_time_model.pkl
#  6. Saves → backend/trained_models/route_metrics.json
#
#  INPUT FEATURES (11) — DIFFERENT FROM WATER & WASTE:
#  Distance_km, Vehicle_Capacity_kg, Current_Load_kg,
#  Fuel_Consumption_km_per_l, Traffic_Congestion_Level,
#  Road_Type, Road_Condition, One_Way_Flag, Toll_Road,
#  Vehicle_Location_Lat, Vehicle_Location_Long
#
#  TARGET:  Travel_Time_min  (minutes per road segment)
#  RANGE:   5 → 180 minutes
#
#  HOW THIS CONNECTS TO FILE 5 (route_optimizer.py):
#  ┌──────────────────────────────────────────────────┐
#  │  Route optimizer has a list of collection stops  │
#  │  e.g. [Stop A, Stop B, Stop C, Stop D]           │
#  │                                                  │
#  │  For every pair of stops it asks this model:     │
#  │  "How long will it take to drive A → B?"         │
#  │  "How long will it take to drive A → C?"  etc.   │
#  │                                                  │
#  │  This builds a COST MATRIX:                      │
#  │       A    B    C    D                           │
#  │  A  [ 0   25   40   15 ]  minutes               │
#  │  B  [25    0   20   35 ]                         │
#  │  C  [40   20    0   30 ]                         │
#  │  D  [15   35   30    0 ]                         │
#  │                                                  │
#  │  Then 2-opt finds the shortest path through all  │
#  └──────────────────────────────────────────────────┘
# ================================================================

import os
import sys
import json
import numpy as np
import joblib

# ----------------------------------------------------------------
#  CONNECT TO FILE 1
# ----------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)

# ← CHAIN LINK TO FILE 1
from src.data_processing.preprocess import run_preprocessing

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics  import mean_absolute_error, mean_squared_error, r2_score

MODELS_DIR = os.path.join(BASE_DIR, "backend", "trained_models")


# ================================================================
#  EVALUATION FUNCTION
#  Unit = minutes
#  e.g. MAE=14 means predictions are off by 14 minutes on average
# ================================================================
def evaluate(name, model, X_test, y_test):
    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    rmse  = np.sqrt(mean_squared_error(y_test, preds))
    r2    = r2_score(y_test, preds)

    print(f"\n  [{name}]")
    print(f"    MAE  = {mae:.4f}  minutes avg error")
    print(f"    RMSE = {rmse:.4f}  minutes")
    print(f"    R²   = {r2:.4f}")

    return {"name": name, "mae": mae, "rmse": rmse, "r2": r2}


# ================================================================
#  MAIN TRAINING FUNCTION
# ================================================================
def train_travel_time_model():
    print("="*55)
    print("  FILE 4 — TRAVEL TIME MODEL TRAINING")
    print("="*55)

    # ── STEP 1: GET DATA FROM FILE 1 ────────────────────────────
    # We pick data["route"] → 11 road/vehicle features
    # This is the THIRD different slice of the same dataset
    # Water  → demographics + weather  (16 features)
    # Waste  → waste history           (19 features)
    # Route  → road + vehicle          (11 features)
    print("\n[1] Calling preprocess.py ...")
    data = run_preprocessing()

    # ← KEY DIFFERENCE FROM FILES 2 & 3
    X_train, X_test, y_train, y_test, scaler = data["route"]

    print(f"\n[2] Route training data ready:")
    print(f"    X_train shape : {X_train.shape}  (8000 rows × 11 features)")
    print(f"    X_test  shape : {X_test.shape}   (2000 rows × 11 features)")
    print(f"    y_train range : {y_train.min():.1f} → {y_train.max():.1f} minutes")
    print(f"    y_test  range : {y_test.min():.1f} → {y_test.max():.1f} minutes")
    print(f"\n    NOTE: This model scores road segments.")
    print(f"    Lower predicted time = faster road = optimizer prefers it")
    print(f"    Used by FILE 5 (route_optimizer.py) to build cost matrix")

    # ── STEP 2: TRAIN 3 MODELS ───────────────────────────────────
    print("\n[3] Training 3 models on route data...")
    trained = {}

    # MODEL A — Random Forest
    # Handles the mix of continuous (Distance_km, Lat, Long)
    # and categorical (Road_Type, Road_Condition, Traffic) well
    print("\n  Training Random Forest ...")
    rf = RandomForestRegressor(
        n_estimators      = 200,
        max_depth         = 10,
        min_samples_split = 5,
        random_state      = 42,
        n_jobs            = -1
    )
    rf.fit(X_train, y_train)
    trained["RandomForest"] = rf

    # MODEL B — Gradient Boosting
    # Good at learning: High traffic + Poor road = much more time
    # (interaction effects between features)
    print("  Training Gradient Boosting ...")
    gb = GradientBoostingRegressor(
        n_estimators  = 200,
        learning_rate = 0.05,
        max_depth     = 4,
        subsample     = 0.8,
        random_state  = 42
    )
    gb.fit(X_train, y_train)
    trained["GradientBoosting"] = gb

    # MODEL C — XGBoost
    # Best at combining Distance + Traffic + Road_Condition
    # into accurate travel time predictions
    try:
        from xgboost import XGBRegressor
        print("  Training XGBoost ...")
        xgb = XGBRegressor(
            n_estimators     = 300,
            learning_rate    = 0.05,
            max_depth        = 5,
            subsample        = 0.8,
            colsample_bytree = 0.8,
            random_state     = 42,
            verbosity        = 0
        )
        xgb.fit(X_train, y_train)
        trained["XGBoost"] = xgb
    except ImportError:
        print("  XGBoost not found → run: pip install xgboost")

    # ── STEP 3: EVALUATE ALL MODELS ─────────────────────────────
    print("\n[4] Evaluating all models on TEST set (2000 unseen rows):")
    print("-"*45)
    results = []
    for name, model in trained.items():
        metrics = evaluate(name, model, X_test, y_test)
        metrics["model_obj"] = model
        results.append(metrics)

    # ── STEP 4: PICK BEST MODEL ──────────────────────────────────
    best = min(results, key=lambda x: x["mae"])
    print(f"\n[5] Best model → {best['name']}")
    print(f"    MAE  = {best['mae']:.4f} minutes")
    print(f"    RMSE = {best['rmse']:.4f} minutes")
    print(f"    R²   = {best['r2']:.4f}")

    # ── STEP 5: SAVE BEST MODEL ──────────────────────────────────
    # Saved to backend/trained_models/travel_time_model.pkl
    #
    # CHAIN: this file → route_optimizer.py → decision_logic.py
    #
    # route_optimizer.py loads this model and calls:
    #   model.predict([distance, traffic, road_type, ...])
    #   → gets predicted minutes for each road segment
    #   → builds cost matrix
    #   → runs 2-opt to find shortest route
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "travel_time_model.pkl")
    joblib.dump(best["model_obj"], model_path)
    print(f"\n[6] 💾 travel_time_model.pkl saved")
    print(f"       → {model_path}")
    print(f"       → loaded later by route_optimizer.py (FILE 5)")

    # ── STEP 6: SAVE METRICS ─────────────────────────────────────
    metrics_out = {
        "model_type"    : best["name"],
        "mae"           : round(best["mae"],  4),
        "rmse"          : round(best["rmse"], 4),
        "r2"            : round(best["r2"],   4),
        "target"        : "Travel_Time_min",
        "unit"          : "minutes",
        "features_used" : 11,
        "train_rows"    : int(X_train.shape[0]),
        "test_rows"     : int(X_test.shape[0]),
        "note"          : "Used by route_optimizer to score road segments",
        "all_models"    : [
            {
                "name": r["name"],
                "mae" : round(r["mae"], 4),
                "r2"  : round(r["r2"],  4)
            }
            for r in results
        ]
    }
    metrics_path = os.path.join(MODELS_DIR, "route_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_out, f, indent=2)
    print(f"    📊 route_metrics.json saved")
    print(f"       → displayed in frontend dashboard")

    print(f"\n{'='*55}")
    print(f"  ✅ TRAVEL TIME MODEL TRAINING COMPLETE")
    print(f"{'='*55}\n")

    return best["model_obj"], metrics_out


# ================================================================
#  RUN DIRECTLY:
#  python src/models/train_travel_time_model.py
# ================================================================
if __name__ == "__main__":
    train_travel_time_model()