import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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

@app.on_event("startup")
async def startup():
    engine.load_models()

class WaterPayload(BaseModel):
    Area_ID: int = 1
    Population: int = 50000
    Population_Density: float = 5000
    Household_Size: int = 4
    Per_Capita_Income: int = 300000
    Urban_Rural_Type: str = "Urban"
    Temperature_C: float = 30.0
    Rainfall_mm: float = 100.0
    Humidity_percent: float = 60.0
    Season: str = "Summer"
    Day_Type: str = "Weekday"
    Festival_Event: str = "None"
    Disaster_Event: str = "None"
    Past_Water_Usage: float = 300.0
    Recycling_Rate_percent: float = 30.0
    month: int = 4
    dayofweek: int = 2
    dayofyear: int = 102

class WastePayload(BaseModel):
    Area_ID: int = 1
    Population: int = 50000
    Population_Density: float = 5000
    Household_Size: int = 4
    Per_Capita_Income: int = 300000
    Urban_Rural_Type: str = "Urban"
    Temperature_C: float = 30.0
    Rainfall_mm: float = 100.0
    Humidity_percent: float = 60.0
    Season: str = "Summer"
    Day_Type: str = "Weekday"
    Festival_Event: str = "None"
    Disaster_Event: str = "None"
    Past_Waste_t1_tons: float = 150.0
    Past_Waste_t7_tons: float = 1050.0
    Past_Waste_t30_tons: float = 4500.0
    Organic_Waste_percent: float = 50.0
    Plastic_Waste_percent: float = 20.0
    Paper_Waste_percent: float = 10.0
    Other_Waste_percent: float = 10.0
    Collection_Frequency_per_week: int = 3
    Recycling_Rate_percent: float = 30.0
    month: int = 4
    dayofweek: int = 2
    dayofyear: int = 102

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

@app.post("/predict/water")
def predict_water(payload: WaterPayload):
    if not engine.ready:
        raise HTTPException(503, "Models not trained.")
    return {"success": True, "prediction": engine.predict_water(payload.dict())}

@app.post("/predict/waste")
def predict_waste(payload: WastePayload):
    if not engine.ready:
        raise HTTPException(503, "Models not trained.")
    return {"success": True, "prediction": engine.predict_waste(payload.dict())}

@app.post("/optimize")
def optimize(payload: RoutePayload):
    stops = []
    for s in payload.stops:
        d = s.dict()
        d["road_type"] = d.pop("road_type_str", "Main_Road")  # fix key name
        stops.append(d)
    vehicle = payload.vehicle.dict()
    result = optimize_route(stops, vehicle)  # fix: only 2 args
    return {"success": True, "optimization": result}

@app.get("/")
def root():
    return {"service": "Smart Waste AI", "status": "running"}