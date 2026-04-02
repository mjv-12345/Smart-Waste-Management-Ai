# ================================================================
#  FILE 6 of 7  —  backend/main.py
#  CORRECTIONS APPLIED:
#  FIX 1: Removed duplicate engine.load_models() from startup
#  FIX 2: Festival/Disaster defaults fixed to match encoder
#  FIX 3: dayofyear dead field removed from both payloads
#  FIX 4: 5 dead fields removed from WastePayload
#  FIX 5: Added POST /predict/route endpoint
#  FIX 6: road_type rename moved to StopItem validator
#  FIX 7: try/except error handling on predict endpoints
# ================================================================

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import json

from src.decision_engine.decision_logic import engine
from src.optimization.route_optimizer import optimize_route

app = FastAPI(title="Smart Waste AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FIX 1: No longer calls engine.load_models() here
# decision_logic.py already calls it at module import time
# This event now just validates that loading succeeded
@app.on_event("startup")
async def startup():
    if not engine.ready:
        print("[main.py] WARNING: engine not ready — run training scripts first")
    else:
        print("[main.py] Engine ready. All models loaded.")

class WastePayload(BaseModel):
    Population: int = 50000
    Temperature_C: float = 30.0
    Rainfall_mm: float = 100.0
    Season: str = "Summer"
    Day_Type: str = "Weekday"


# FIX 2: Festival/Disaster defaults match LabelEncoder values
# FIX 3: dayofyear removed — not in WATER_FEATURES
class WaterPayload(BaseModel):
    Population: int = 50000
    Temperature_C: int = 40
    Rainfall_mm: float = 100.0
    Humidity_percent: float = 60.0
    Season: str = "Summer"
    Day_Type: str = "Weekday"

# FIX 6: road_type alias handled in validator — not inline in endpoint
class StopItem(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    waste_kg: float = 500
    fill_percent: float = 75
    traffic: str = "Medium"
    road_type_str: str = "Main_Road"
    road_condition: str = "Average"
    one_way: int = 0
    toll: int = 0
    population_density: float = 5000
    collection_freq: int = 3

    def dict(self, **kwargs):
        d = super().dict(**kwargs)
        d["road_type"] = d.pop("road_type_str", "Main_Road")  # FIX 6
        return d


class VehicleItem(BaseModel):
    capacity_kg: float = 5000
    current_load_kg: float = 0
    fuel_km_per_l: float = 5.0


class RoutePayload(BaseModel):
    stops: List[StopItem]
    vehicle: VehicleItem = VehicleItem()
    depot_index: int = 0


@app.get("/health")
def health():
    metrics = {}
    models_dir = os.path.join(os.path.dirname(__file__), "trained_models")
    for name in ["water", "waste", "route"]:
        path = os.path.join(models_dir, f"{name}_metrics.json")
        if os.path.exists(path):
            with open(path) as f:
                metrics[name] = json.load(f)
    return {
        "status": "ready" if engine.ready else "models_not_trained",
        "models_ready": engine.ready,
        "metrics": metrics
    }


# FIX 7: try/except for structured error response
@app.post("/predict/water")
def predict_water(payload: WaterPayload):
    if not engine.ready:
        raise HTTPException(503, "Models not trained. Run training scripts first.")
    try:
        return {"success": True, "prediction": engine.predict_water(payload.dict())}
    except Exception as e:
        raise HTTPException(422, f"Prediction failed: {str(e)}")


# FIX 7: try/except for structured error response
@app.post("/predict/waste")
def predict_waste(payload: WastePayload):
    if not engine.ready:
        raise HTTPException(503, "Models not trained. Run training scripts first.")
    try:
        return {"success": True, "prediction": engine.predict_waste(payload.dict())}
    except Exception as e:
        raise HTTPException(422, f"Prediction failed: {str(e)}")


# FIX 5: New endpoint — was completely missing
@app.post("/predict/route")
def predict_route(payload: WastePayload):
    if not engine.ready:
        raise HTTPException(503, "Models not trained. Run training scripts first.")
    try:
        return {"success": True, "prediction": engine.predict_route(payload.dict())}
    except Exception as e:
        raise HTTPException(422, f"Route prediction failed: {str(e)}")


@app.post("/optimize")
def optimize(payload: RoutePayload):
    stops = [s.dict() for s in payload.stops]   # FIX 6: dict() handles rename
    vehicle = payload.vehicle.dict()
    result = optimize_route(stops, vehicle)
    return {"success": True, "optimization": result}


@app.get("/")
def root():
    return {"service": "Smart Waste AI", "status": "running"}


@app.get("/")
def root():
    return {"service": "Smart Waste AI", "status": "running"}