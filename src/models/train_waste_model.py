# ================================================================
#  FILE 3 of 7  —  src/models/train_waste_model.py
#
#  CORRECTIONS APPLIED:
#  1. Added n_jobs=-1 to XGBRegressor (parallel training)
#  2. Added feature_importances_ export to metrics JSON
#  3. Added explicit logging when XGBoost is skipped
# ================================================================

import os
import sys
import json
import numpy as np
import joblib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)

from src.data_processing.preprocess import run_preprocessing

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics  import mean_absolute_error, mean_squared_error, r2_score

MODELS_DIR = os.path.join(BASE_DIR, "backend", "trained_models")

WASTE_FEATURE_NAMES = [
    "Population", "Population_Density", "Temperature_C",
    "Rainfall_mm", "Season", "Day_Type", "Festival_Event",
    "Disaster_Event", "Past_Waste_t1_tons", "Past_Waste_t7_tons",
    "Past_Waste_t30_tons", "Organic_Waste_percent",
    "Plastic_Waste_percent", "Paper_Waste_percent",
    "Other_Waste_percent", "Collection_Frequency_per_week",
    "Recycling_Rate_percent", "month", "dayofweek"
]


# ================================================================
#  EVALUATION FUNCTION
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
    print("\n[1] Calling preprocess.py ...")
    data = run_preprocessing()

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
    # FIX 1: Added n_jobs=-1 for parallel training speed
    # FIX 3: Explicit logging when XGBoost is skipped
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
            n_jobs           = -1,   # FIX 1: parallel training
            verbosity        = 0
        )
        xgb.fit(X_train, y_train)
        trained["XGBoost"] = xgb
    except ImportError:
        # FIX 3: explicit fallback logging instead of silent skip
        print("  ⚠️  XGBoost not installed — skipping.")
        print("      Best model will be selected from 2 remaining models.")
        print("      To include XGBoost: pip install xgboost")

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
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "waste_model.pkl")
    joblib.dump(best["model_obj"], model_path)
    print(f"\n[6] 💾 waste_model.pkl saved")
    print(f"       → {model_path}")
    print(f"       → loaded later by decision_logic.py")

    # ── STEP 6: SAVE METRICS ─────────────────────────────────────
    # FIX 2: Extract and save feature importances
    best_model = best["model_obj"]
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        feature_importance_dict = {
            name: round(float(score), 6)
            for name, score in zip(WASTE_FEATURE_NAMES, importances)
        }
        # Sort by importance descending for easy reading
        feature_importance_dict = dict(
            sorted(feature_importance_dict.items(),
                   key=lambda x: x[1], reverse=True)
        )
    else:
        feature_importance_dict = {}
        print("    ⚠️  Model does not expose feature_importances_")

    metrics_out = {
        "model_type"          : best["name"],
        "mae"                 : round(best["mae"],  4),
        "rmse"                : round(best["rmse"], 4),
        "r2"                  : round(best["r2"],   4),
        "target"              : "Waste_Generated_tons",
        "unit"                : "tonnes/day",
        "features_used"       : 19,
        "train_rows"          : int(X_train.shape[0]),
        "test_rows"           : int(X_test.shape[0]),
        "feature_importances" : feature_importance_dict,   # FIX 2
        "all_models"          : [
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
    print(f"       → includes feature importances (FIX 2)")
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