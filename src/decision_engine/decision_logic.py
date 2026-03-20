# ================================================================
#  FILE 5 of 7  —  src/decision_engine/decision_logic.py
#  CORRECTIONS APPLIED:
#  FIX 1: Added predict_route() method (was completely missing)
#  FIX 2: Added scaler_route.pkl loading (was never loaded)
#  FIX 3: engine.load_models() called at module level
#  FIX 4: Renamed _scaler_g → _scaler_waste for clarity
#  FIX 5: _encode_cat logs warning on unknown category
#  FIX 6: Confidence bounds derived from MAE not magic numbers
#  FIX 7: Ready guard added to all predict methods
# ================================================================

import os
import sys
import json
import numpy as np
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

ROOT          = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
MODELS_DIR    = os.path.join(ROOT, 'backend', 'trained_models')
PROCESSED_DIR = os.path.join(ROOT, 'data', 'processed')


class SmartWasteDecisionEngine:

    def __init__(self):
        self._water_model  = None
        self._waste_model  = None
        self._route_model  = None
        self._scaler_w     = None
        self._scaler_waste = None   # FIX 4: renamed from _scaler_g
        self._scaler_r     = None   # FIX 2: added route scaler
        self._encoders     = None
        self._ready        = False

    def load_models(self):
        errors = []

        def _load(path):
            if not os.path.exists(path):
                errors.append(f'Missing: {path}')
                return None
            return joblib.load(path)

        self._water_model  = _load(os.path.join(MODELS_DIR,    'water_model.pkl'))
        self._waste_model  = _load(os.path.join(MODELS_DIR,    'waste_model.pkl'))
        self._route_model  = _load(os.path.join(MODELS_DIR,    'travel_time_model.pkl'))
        self._scaler_w     = _load(os.path.join(PROCESSED_DIR, 'scaler_water.pkl'))
        self._scaler_waste = _load(os.path.join(PROCESSED_DIR, 'scaler_waste.pkl'))  # FIX 4
        self._scaler_r     = _load(os.path.join(PROCESSED_DIR, 'scaler_route.pkl'))  # FIX 2
        self._encoders     = _load(os.path.join(PROCESSED_DIR, 'label_encoders.pkl'))

        if errors:
            for e in errors:
                print(f'[DecisionEngine] WARNING: {e}')
            self._ready = False
            print('[DecisionEngine] Some files missing — run training scripts first.')
        else:
            self._ready = True
            print('[DecisionEngine] All models loaded successfully.')

    @property
    def ready(self):
        return self._ready

    def _encode_cat(self, val, field):
        if self._encoders is None:
            return 0
        le = self._encoders.get(field)
        if le is None:
            return 0
        try:
            return int(le.transform([str(val)])[0])
        except ValueError:
            # FIX 5: log unknown categories instead of silent return
            print(f'[WARN] Unknown value for {field}="{val}", defaulting to 0')
            return 0

    def _build_row(self, payload, feature_list):
        CAT = {
            'Urban_Rural_Type', 'Season', 'Day_Type', 'Festival_Event',
            'Disaster_Event', 'Traffic_Congestion_Level',
            'Road_Type', 'Road_Condition'
        }
        row = []
        for feat in feature_list:
            val = payload.get(feat, 0)
            if feat in CAT:
                val = self._encode_cat(val, feat)
            row.append(float(val))
        return row

    def _load_mae(self, metrics_file):
        """FIX 6: Load MAE from saved metrics for real confidence bounds."""
        path = os.path.join(MODELS_DIR, metrics_file)
        try:
            with open(path) as f:
                return json.load(f).get('mae', None)
        except Exception:
            return None

    def predict_water(self, payload):
        # FIX 7: guard against unloaded models
        if not self._ready:
            raise RuntimeError('[DecisionEngine] Models not loaded. Call load_models() first.')

        from src.data_processing.preprocess import WATER_FEATURES
        row  = self._build_row(payload, WATER_FEATURES)
        X    = np.array(row).reshape(1, -1)
        X    = self._scaler_w.transform(X)
        pred = float(self._water_model.predict(X)[0])

        # FIX 6: MAE-derived bounds instead of magic numbers
        mae   = self._load_mae('water_metrics.json')
        delta = mae if mae else pred * 0.10
        return {
            'water_demand_liters': round(pred, 2),
            'lower_bound':         round(max(0, pred - delta), 2),
            'upper_bound':         round(pred + delta, 2),
        }

    def predict_waste(self, payload):
        # FIX 7: guard against unloaded models
        if not self._ready:
            raise RuntimeError('[DecisionEngine] Models not loaded. Call load_models() first.')

        from src.data_processing.preprocess import WASTE_FEATURES
        row  = self._build_row(payload, WASTE_FEATURES)
        X    = np.array(row).reshape(1, -1)
        X    = self._scaler_waste.transform(X)   # FIX 4: renamed
        pred = float(self._waste_model.predict(X)[0])

        # FIX 6: MAE-derived bounds
        mae   = self._load_mae('waste_metrics.json')
        delta = mae if mae else pred * 0.12
        return {
            'waste_generated_tons': round(pred, 3),
            'lower_bound':          round(max(0, pred - delta), 3),
            'upper_bound':          round(pred + delta, 3),
        }

    def predict_route(self, payload):
        # FIX 1: this method was completely missing
        # FIX 7: guard against unloaded models
        if not self._ready:
            raise RuntimeError('[DecisionEngine] Models not loaded. Call load_models() first.')

        from src.data_processing.preprocess import ROUTE_FEATURES
        row  = self._build_row(payload, ROUTE_FEATURES)
        X    = np.array(row).reshape(1, -1)
        X    = self._scaler_r.transform(X)       # FIX 2: scaler_route
        pred = float(self._route_model.predict(X)[0])

        # FIX from FILE 4: travel time cannot be negative
        pred = max(0.0, pred)

        mae   = self._load_mae('route_metrics.json')
        delta = mae if mae else pred * 0.10
        return {
            'travel_time_minutes': round(pred, 2),
            'lower_bound':         round(max(0, pred - delta), 2),
            'upper_bound':         round(pred + delta, 2),
        }


# FIX 3: load_models() called at module level so engine is
# ready when backend/main.py imports this file
engine = SmartWasteDecisionEngine()
engine.load_models()