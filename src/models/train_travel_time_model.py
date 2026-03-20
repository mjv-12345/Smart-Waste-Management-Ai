# ================================================================
#  FILE 4 of 7  —  src/models/train_travel_time_model.py
#  CORRECTIONS APPLIED:
#  FIX 1: Added n_jobs=-1 to XGBRegressor
#  FIX 2: Added feature_importances_ export to metrics JSON
#  FIX 3: Explicit XGBoost fallback logging
#  FIX 4: Added ROUTE_FEATURE_NAMES list
#  FIX 5: Added prediction clipping warning comment
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
ROUTE_FEATURE_NAMES = [
    "Distance_km", "Vehicle_Capacity_kg", "Current_Load_kg",
    "Fuel_Consumption_km_per_l", "Traffic_Congestion_Level",
    "Road_Type", "Road_Condition", "One_Way_Flag",
    "Toll_Road", "Vehicle_Location_Lat", "Vehicle_Location_Long"
]

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

def train_travel_time_model():
    print("="*55)
    print("  FILE 4 — TRAVEL TIME MODEL TRAINING")
    print("="*55)

    print("\n[1] Calling preprocess.py ...")
    data = run_preprocessing()
    X_train, X_test, y_train, y_test, scaler = data["route"]

    print(f"\n[2] Route training data ready:")
    print(f"    X_train : {X_train.shape}  (8000 rows x 11 features)")
    print(f"    X_test  : {X_test.shape}   (2000 rows x 11 features)")
    print(f"    y range : {y_train.min():.1f} to {y_train.max():.1f} minutes")
    print(f"    NOTE: Lower predicted time = faster road = optimizer prefers it")
    # FIX 5: Document clipping requirement for route_optimizer.py
    print(f"    NOTE: route_optimizer.py must clip predictions: np.maximum(0, pred)")

    print("\n[3] Training 3 models on route data...")
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
    print(f"    MAE={best['mae']:.4f} mins  RMSE={best['rmse']:.4f}  R²={best['r2']:.4f}")

    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "travel_time_model.pkl")
    joblib.dump(best["model_obj"], model_path)
    print(f"\n[6] travel_time_model.pkl saved → {model_path}")
    print(f"    → loaded by route_optimizer.py (FILE 5)")

    # FIX 2: Extract and export feature importances
    best_model = best["model_obj"]
    if hasattr(best_model, "feature_importances_"):
        feature_importance_dict = dict(sorted(
            {name: round(float(score), 6)
             for name, score in zip(ROUTE_FEATURE_NAMES,
                                    best_model.feature_importances_)}.items(),
            key=lambda x: x[1], reverse=True
        ))
    else:
        feature_importance_dict = {}

    metrics_out = {
        "model_type"          : best["name"],
        "mae"                 : round(best["mae"],  4),
        "rmse"                : round(best["rmse"], 4),
        "r2"                  : round(best["r2"],   4),
        "target"              : "Travel_Time_min",
        "unit"                : "minutes",
        "features_used"       : 11,
        "train_rows"          : int(X_train.shape[0]),
        "test_rows"           : int(X_test.shape[0]),
        "note"                : "Used by route_optimizer to score road segments. Predictions must be clipped to max(0, pred).",
        "feature_importances" : feature_importance_dict,  # FIX 2
        "all_models"          : [
            {"name": r["name"], "mae": round(r["mae"],4), "r2": round(r["r2"],4)}
            for r in results
        ]
    }
    metrics_path = os.path.join(MODELS_DIR, "route_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_out, f, indent=2)
    print(f"    route_metrics.json saved (includes feature importances)")

    print(f"\n{'='*55}")
    print(f"  TRAVEL TIME MODEL TRAINING COMPLETE")
    print(f"{'='*55}\n")
    return best["model_obj"], metrics_out

if __name__ == "__main__":
    train_travel_time_model()