# ================================================================
#  FILE 2 of 7  —  src/models/train_water_model.py
#  CORRECTIONS APPLIED:
#  FIX 1: Added n_jobs=-1 to XGBRegressor
#  FIX 2: Added feature_importances_ export to metrics JSON
#  FIX 3: Explicit XGBoost fallback logging
#  FIX 4: Added WATER_FEATURE_NAMES list for importance mapping
#  FIX 5: Removed misleading "R²<0 expected" comment
# ================================================================

import os, sys, json
import numpy as np
import joblib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)

from src.data_processing.preprocess import run_preprocessing
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics  import mean_absolute_error, mean_squared_error, r2_score

MODELS_DIR = os.path.join(BASE_DIR, "backend", "trained_models")

# FIX 4: Feature names for importance mapping
WATER_FEATURE_NAMES = [
    "Population", "Population_Density", "Household_Size",
    "Per_Capita_Income", "Urban_Rural_Type", "Temperature_C",
    "Rainfall_mm", "Humidity_percent", "Season", "Day_Type",
    "Festival_Event", "Past_Water_Usage", "Recycling_Rate_percent",
    "Disaster_Event", "month", "dayofweek"
]

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

def train_water_model():
    print("="*55)
    print("  FILE 2 — WATER DEMAND MODEL TRAINING")
    print("="*55)

    print("\n[1] Calling preprocess.py ...")
    data = run_preprocessing()
    X_train, X_test, y_train, y_test, scaler = data["water"]

    print(f"\n[2] Water training data ready:")
    print(f"    X_train : {X_train.shape}  (8000 rows x 16 features)")
    print(f"    X_test  : {X_test.shape}   (2000 rows x 16 features)")
    print(f"    y range : {y_train.min():.1f} to {y_train.max():.1f} litres")

    print("\n[3] Training 3 models on water data...")
    trained = {}

    print("\n  Training Random Forest ...")
    rf = RandomForestRegressor(
        n_estimators=200, max_depth=10,
        min_samples_split=5, random_state=42, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    trained["RandomForest"] = rf

    print("  Training Gradient Boosting ...")
    gb = GradientBoostingRegressor(
        n_estimators=200, learning_rate=0.05,
        max_depth=4, subsample=0.8, random_state=42
    )
    gb.fit(X_train, y_train)
    trained["GradientBoosting"] = gb

    # FIX 1: n_jobs=-1 added | FIX 3: explicit fallback logging
    try:
        from xgboost import XGBRegressor
        print("  Training XGBoost ...")
        xgb = XGBRegressor(
            n_estimators=300, learning_rate=0.05,
            max_depth=5, subsample=0.8,
            colsample_bytree=0.8, random_state=42,
            n_jobs=-1,   # FIX 1: parallel training
            verbosity=0
        )
        xgb.fit(X_train, y_train)
        trained["XGBoost"] = xgb
    except ImportError:
        # FIX 3: explicit fallback logging
        print("  XGBoost SKIPPED — not installed.")
        print("  Best model selected from 2 remaining models.")
        print("  To include XGBoost: pip install xgboost")

    print("\n[4] Evaluating all models on TEST set (2000 unseen rows):")
    print("-"*45)
    results = []
    for name, model in trained.items():
        metrics = evaluate(name, model, X_test, y_test)
        metrics["model_obj"] = model
        results.append(metrics)

    best = min(results, key=lambda x: x["mae"])
    print(f"\n[5] Best model: {best['name']}")
    print(f"    MAE={best['mae']:.4f}  RMSE={best['rmse']:.4f}  R²={best['r2']:.4f}")

    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "water_model.pkl")
    joblib.dump(best["model_obj"], model_path)
    print(f"\n[6] water_model.pkl saved → {model_path}")

    # FIX 2: Extract and export feature importances
    best_model = best["model_obj"]
    if hasattr(best_model, "feature_importances_"):
        feature_importance_dict = dict(sorted(
            {name: round(float(score), 6)
             for name, score in zip(WATER_FEATURE_NAMES,
                                    best_model.feature_importances_)}.items(),
            key=lambda x: x[1], reverse=True
        ))
    else:
        feature_importance_dict = {}
        print("    Model does not expose feature_importances_")

    metrics_out = {
        "model_type"          : best["name"],
        "mae"                 : round(best["mae"],  4),
        "rmse"                : round(best["rmse"], 4),
        "r2"                  : round(best["r2"],   4),
        "target"              : "Water_Demand",
        "unit"                : "litres/day",
        "features_used"       : 16,
        "train_rows"          : int(X_train.shape[0]),
        "test_rows"           : int(X_test.shape[0]),
        "feature_importances" : feature_importance_dict,  # FIX 2
        "all_models"          : [
            {"name": r["name"], "mae": round(r["mae"],4), "r2": round(r["r2"],4)}
            for r in results
        ]
    }
    metrics_path = os.path.join(MODELS_DIR, "water_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_out, f, indent=2)
    print(f"    water_metrics.json saved (includes feature importances)")

    print(f"\n{'='*55}")
    print(f"  WATER MODEL TRAINING COMPLETE")
    print(f"{'='*55}\n")
    print(f"  WATER MODEL TRAINING COMPLETE")
    print(f"{'='*55}\n")

# ===== MANUAL TESTING =====
    print("\n===== MANUAL TESTING =====")

    test1 = [[200000, 40, 50, 60, 1, 0]]
    test1_scaled = scaler.transform(test1)
    print("Test 1:", best["model_obj"].predict(test1_scaled))

    test2 = [[50000, 20, 200, 30, 0, 1]]
    test2_scaled = scaler.transform(test2)
    print("Test 2:", best["model_obj"].predict(test2_scaled))

    test3 = [[100000, 30, 100, 50, 2, 0]]
    test3_scaled = scaler.transform(test3)
    print("Test 3:", best["model_obj"].predict(test3_scaled))
    return best["model_obj"], metrics_out
    print("X_train shape:", X_train.shape)
if __name__ == "__main__":
    train_water_model()