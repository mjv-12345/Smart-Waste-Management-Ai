# ================================================================
#  FILE 3 of 7  —  src/models/train_waste_model.py
#
#  ROLE IN THE CHAIN:
#  ┌─────────────────────────────────────────────────────┐
#  │  preprocess.py                                      │
#  │       │  run_preprocessing() → data["waste"]        │
#  │       ▼                                             │
#  │  train_waste_model.py  ◄── YOU ARE HERE             │
#  │       │                                             │
#  │       ▼                                             │
#  │  backend/trained_models/waste_model.pkl             │
#  │       │                                             │
#  │       ▼  (loaded later by)                          │
#  │  decision_logic.py → backend/main.py                │
#  └─────────────────────────────────────────────────────┘
#
#  WHAT THIS FILE DOES:
#  1. Calls preprocess.py → gets clean waste training data
#  2. Trains 3 different ML algorithms
#  3. Tests each on 2000 unseen rows
#  4. Picks the best model automatically
#  5. Saves best model → backend/trained_models/waste_model.pkl
#  6. Saves metrics  → backend/trained_models/waste_metrics.json
#
#  INPUT FEATURES (19) — DIFFERENT FROM WATER MODEL:
#  Population, Population_Density, Temperature_C,
#  Rainfall_mm, Season, Day_Type, Festival_Event,
#  Disaster_Event, Past_Waste_t1_tons, Past_Waste_t7_tons,
#  Past_Waste_t30_tons, Organic_Waste_percent,
#  Plastic_Waste_percent, Paper_Waste_percent,
#  Other_Waste_percent, Collection_Frequency_per_week,
#  Recycling_Rate_percent, month, dayofweek
#
#  TARGET:  Waste_Generated_tons  (tonnes/day)
#  RANGE:   25 → 250 tonnes
#
#  WHY DIFFERENT FROM WATER MODEL?
#  Water demand depends on WHO lives there (demographics)
#  Waste generation depends on WHAT was generated before
#  (history + composition) — completely different signal set
# ================================================================

import os
import sys
import json
import numpy as np
import joblib

# ----------------------------------------------------------------
#  CONNECT TO FILE 1
#  Add project root to path so imports work correctly
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
#  Same logic as water model but unit = tonnes
# ================================================================
def evaluate(name, model, X_test, y_test):
    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    rmse  = np.sqrt(mean_squared_error(y_test, preds))
    r2    = r2_score(y_test, preds)

    print(f"\n  [{name}]")
    print(f"    MAE  = {mae:.4f}  tonnes avg error")
    print(f"    RMSE = {rmse:.4f}  tonnes")
    print(f"    R²   = {r2:.4f}")

    return {"name": name, "mae": mae, "rmse": rmse, "r2": r2}


# ================================================================
#  MAIN TRAINING FUNCTION
# ================================================================
def train_waste_model():
    print("="*55)
    print("  FILE 3 — WASTE GENERATION MODEL TRAINING")
    print("="*55)

    # ── STEP 1: GET DATA FROM FILE 1 ────────────────────────────
    # Same call as water model but we pick data["waste"]
    # This gives us 19 waste-specific features
    print("\n[1] Calling preprocess.py ...")
    data = run_preprocessing()

    # ← KEY DIFFERENCE FROM FILE 2
    # Water model used data["water"] with 16 features
    # Waste model uses data["waste"] with 19 features
    X_train, X_test, y_train, y_test, scaler = data["waste"]

    print(f"\n[2] Waste training data ready:")
    print(f"    X_train shape : {X_train.shape}  (8000 rows × 19 features)")
    print(f"    X_test  shape : {X_test.shape}   (2000 rows × 19 features)")
    print(f"    y_train range : {y_train.min():.1f} → {y_train.max():.1f} tonnes")
    print(f"    y_test  range : {y_test.min():.1f} → {y_test.max():.1f} tonnes")

    # ── STEP 2: TRAIN 3 MODELS ───────────────────────────────────
    print("\n[3] Training 3 models on waste data...")
    trained = {}

    # MODEL A — Random Forest
    # 200 trees, each sees random subset of
    # 19 waste features (history + composition + collection)
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
    # Sequentially corrects errors
    # Works well with the rolling waste history columns
    # (Past_Waste_t1, t7, t30 have strong sequential patterns)
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
    # Best at handling the waste composition percentages
    # (Organic%, Plastic%, Paper%, Other% — all related)
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
    print(f"    MAE  = {best['mae']:.4f} tonnes")
    print(f"    RMSE = {best['rmse']:.4f} tonnes")
    print(f"    R²   = {best['r2']:.4f}")

    # ── STEP 5: SAVE BEST MODEL ──────────────────────────────────
    # Saved to backend/trained_models/waste_model.pkl
    # Chain: this file → decision_logic.py → main.py → frontend
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "waste_model.pkl")
    joblib.dump(best["model_obj"], model_path)
    print(f"\n[6] 💾 waste_model.pkl saved")
    print(f"       → {model_path}")
    print(f"       → loaded later by decision_logic.py")

    # ── STEP 6: SAVE METRICS ─────────────────────────────────────
    metrics_out = {
        "model_type"    : best["name"],
        "mae"           : round(best["mae"],  4),
        "rmse"          : round(best["rmse"], 4),
        "r2"            : round(best["r2"],   4),
        "target"        : "Waste_Generated_tons",
        "unit"          : "tonnes/day",
        "features_used" : 19,
        "train_rows"    : int(X_train.shape[0]),
        "test_rows"     : int(X_test.shape[0]),
        "all_models"    : [
            {
                "name": r["name"],
                "mae" : round(r["mae"], 4),
                "r2"  : round(r["r2"],  4)
            }
            for r in results
        ]
    }
    metrics_path = os.path.join(MODELS_DIR, "waste_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_out, f, indent=2)
    print(f"    📊 waste_metrics.json saved")
    print(f"       → displayed in frontend dashboard")

    print(f"\n{'='*55}")
    print(f"  ✅ WASTE MODEL TRAINING COMPLETE")
    print(f"{'='*55}\n")

    return best["model_obj"], metrics_out


# ================================================================
#  RUN DIRECTLY:
#  python src/models/train_waste_model.py
# ================================================================
if __name__ == "__main__":
    train_waste_model()