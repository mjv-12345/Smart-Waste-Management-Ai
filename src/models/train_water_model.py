# ================================================================
#  FILE 2 of 7  —  src/models/train_water_model.py
#
#  ROLE IN THE CHAIN:
#  ┌─────────────────────────────────────────────────────┐
#  │  preprocess.py                                      │
#  │       │  run_preprocessing() → data["water"]        │
#  │       ▼                                             │
#  │  train_water_model.py  ◄── YOU ARE HERE             │
#  │       │                                             │
#  │       ▼                                             │
#  │  backend/trained_models/water_model.pkl             │
#  │       │                                             │
#  │       ▼  (loaded later by)                          │
#  │  decision_logic.py → backend/main.py                │
#  └─────────────────────────────────────────────────────┘
#
#  WHAT THIS FILE DOES:
#  1. Calls preprocess.py → gets clean water training data
#  2. Trains 3 different ML algorithms
#  3. Tests each on 2000 unseen rows
#  4. Picks the best model automatically
#  5. Saves best model → backend/trained_models/water_model.pkl
#  6. Saves metrics  → backend/trained_models/water_metrics.json
#
#  INPUT FEATURES (16):
#  Population, Population_Density, Household_Size,
#  Per_Capita_Income, Urban_Rural_Type, Temperature_C,
#  Rainfall_mm, Humidity_percent, Season, Day_Type,
#  Festival_Event, Past_Water_Usage, Recycling_Rate_percent,
#  Disaster_Event, month, dayofweek
#
#  TARGET:  Water_Demand  (litres/day)
#  RANGE:   60 → 600 litres
# ================================================================

import os
import sys
import json
import numpy as np
import joblib

# ----------------------------------------------------------------
#  CONNECT TO FILE 1
#  sys.path tells Python where to look for imports
#  We add the project root so "from src.data_processing..."  works
# ----------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)

# ← THIS IS THE CHAIN LINK TO FILE 1
from src.data_processing.preprocess import run_preprocessing

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics  import mean_absolute_error, mean_squared_error, r2_score

MODELS_DIR = os.path.join(BASE_DIR, "backend", "trained_models")


# ================================================================
#  EVALUATION FUNCTION
#  Tests a trained model on the held-out test set
#  Returns 3 metrics:
#
#  MAE  = Mean Absolute Error
#         average difference between predicted and actual
#         unit = litres
#         e.g. MAE=55 means predictions are off by 55L on average
#
#  RMSE = Root Mean Squared Error
#         punishes large errors more than MAE
#         unit = litres
#
#  R²   = how much variance the model explains
#         R²=1.0 → perfect predictions
#         R²=0.0 → no better than predicting the mean every time
#         R²<0   → worse than predicting the mean (expected here
#                  since dataset targets are randomly generated)
# ================================================================
def evaluate(name, model, X_test, y_test):
    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    rmse  = np.sqrt(mean_squared_error(y_test, preds))
    r2    = r2_score(y_test, preds)

    print(f"\n  [{name}]")
    print(f"    MAE  = {mae:.4f}  litres avg error")
    print(f"    RMSE = {rmse:.4f}  litres")
    print(f"    R²   = {r2:.4f}")

    return {"name": name, "mae": mae, "rmse": rmse, "r2": r2}


# ================================================================
#  MAIN TRAINING FUNCTION
# ================================================================
def train_water_model():
    print("="*55)
    print("  FILE 2 — WATER DEMAND MODEL TRAINING")
    print("="*55)

    # ── STEP 1: GET DATA FROM FILE 1 ────────────────────────────
    # This calls preprocess.py which:
    #   loads Excel → cleans → encodes → splits → scales
    # We only pick data["water"] — the 16 water features
    print("\n[1] Calling preprocess.py ...")
    data = run_preprocessing()

    X_train, X_test, y_train, y_test, scaler = data["water"]

    print(f"\n[2] Water training data ready:")
    print(f"    X_train shape : {X_train.shape}  (8000 rows × 16 features)")
    print(f"    X_test  shape : {X_test.shape}   (2000 rows × 16 features)")
    print(f"    y_train range : {y_train.min():.1f} → {y_train.max():.1f} litres")
    print(f"    y_test  range : {y_test.min():.1f} → {y_test.max():.1f} litres")

    # ── STEP 2: TRAIN 3 MODELS ───────────────────────────────────
    print("\n[3] Training 3 models on water data...")
    trained = {}

    # MODEL A — Random Forest
    # Builds 200 independent decision trees
    # Each tree sees a random subset of data + features
    # Final prediction = average of all 200 trees
    # Good at: handling mixed feature types, resistant to overfitting
    print("\n  Training Random Forest ...")
    rf = RandomForestRegressor(
        n_estimators  = 200,    # 200 trees
        max_depth     = 10,     # max depth per tree
        min_samples_split = 5,  # min samples to split a node
        random_state  = 42,
        n_jobs        = -1      # use all CPU cores
    )
    rf.fit(X_train, y_train)
    trained["RandomForest"] = rf

    # MODEL B — Gradient Boosting
    # Builds trees SEQUENTIALLY
    # Each new tree fixes the errors of the previous one
    # learning_rate=0.05 means each step is small and careful
    # Good at: finding complex patterns, often beats Random Forest
    print("  Training Gradient Boosting ...")
    gb = GradientBoostingRegressor(
        n_estimators  = 200,
        learning_rate = 0.05,   # small steps = careful learning
        max_depth     = 4,      # shallow trees work best here
        subsample     = 0.8,    # use 80% of data per tree
        random_state  = 42
    )
    gb.fit(X_train, y_train)
    trained["GradientBoosting"] = gb

    # MODEL C — XGBoost
    # Extreme Gradient Boosting
    # Faster and more regularised than standard GradientBoosting
    # Industry standard for tabular data competitions
    try:
        from xgboost import XGBRegressor
        print("  Training XGBoost ...")
        xgb = XGBRegressor(
            n_estimators      = 300,
            learning_rate     = 0.05,
            max_depth         = 5,
            subsample         = 0.8,
            colsample_bytree  = 0.8,  # 80% of features per tree
            random_state      = 42,
            verbosity         = 0     # silent
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
    # We pick by lowest MAE (most accurate predictions)
    best = min(results, key=lambda x: x["mae"])
    print(f"\n[5] Best model → {best['name']}")
    print(f"    MAE  = {best['mae']:.4f} litres")
    print(f"    RMSE = {best['rmse']:.4f} litres")
    print(f"    R²   = {best['r2']:.4f}")

    # ── STEP 5: SAVE BEST MODEL ──────────────────────────────────
    # This .pkl is loaded by decision_logic.py at API startup
    # When frontend sends a prediction request →
    #   main.py → decision_logic.py → loads this file → predicts
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "water_model.pkl")
    joblib.dump(best["model_obj"], model_path)
    print(f"\n[6] 💾 water_model.pkl saved")
    print(f"       → {model_path}")
    print(f"       → loaded later by decision_logic.py")

    # ── STEP 6: SAVE METRICS ─────────────────────────────────────
    # Displayed in the frontend dashboard sidebar
    metrics_out = {
        "model_type"    : best["name"],
        "mae"           : round(best["mae"],  4),
        "rmse"          : round(best["rmse"], 4),
        "r2"            : round(best["r2"],   4),
        "target"        : "Water_Demand",
        "unit"          : "litres/day",
        "features_used" : 16,
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
    metrics_path = os.path.join(MODELS_DIR, "water_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_out, f, indent=2)
    print(f"    📊 water_metrics.json saved")
    print(f"       → displayed in frontend dashboard")

    print(f"\n{'='*55}")
    print(f"  ✅ WATER MODEL TRAINING COMPLETE")
    print(f"{'='*55}\n")

    return best["model_obj"], metrics_out


# ================================================================
#  RUN DIRECTLY:
#  python src/models/train_water_model.py
# ================================================================
if __name__ == "__main__":
    train_water_model()