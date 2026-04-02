# ================================================================
#  FILE 1 of 7  —  src/data_processing/preprocess.py
#
#  ROLE IN THE CHAIN:
#  ┌─────────────────────────────────────────────────────┐
#  │  smart_city_dataset.xlsx                            │
#  │           │                                         │
#  │           ▼                                         │
#  │    preprocess.py   ◄── YOU ARE HERE                 │
#  │           │                                         │
#  │    saves .pkl files to  data/processed/             │
#  │    returns clean data to  train_*.py  files         │
#  └─────────────────────────────────────────────────────┘
#
#  HOW OTHER FILES USE THIS:
#  Every training file starts with this exact line:
#
#    from src.data_processing.preprocess import run_preprocessing
#    data = run_preprocessing()
#
#  Then each file picks its model's data:
#    data["water"]  →  used by train_water_model.py
#    data["waste"]  →  used by train_waste_model.py
#    data["route"]  →  used by train_travel_time_model.py
#
#  WHAT THIS FILE OUTPUTS:
#  ┌─────────────────────────────────────────────────────┐
#  │  data/processed/                                    │
#  │    ├── label_encoders.pkl  (text → number maps)     │
#  │    ├── scaler_water.pkl    (water feature scaler)   │
#  │    ├── scaler_waste.pkl    (waste feature scaler)   │
#  │    └── scaler_route.pkl    (route feature scaler)   │
#  └─────────────────────────────────────────────────────┘
#  These .pkl files are later loaded by:
#    decision_logic.py  → to encode/scale live API inputs
# ================================================================

import os
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split

# ----------------------------------------------------------------
#  PATHS
#  This file lives at:  src/data_processing/preprocess.py
#  BASE_DIR goes up 2 levels → project root (SMART-WA folder)
# ----------------------------------------------------------------
BASE_DIR      = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../../")
                )
DATA_PATH     = os.path.join(BASE_DIR, "data", "raw", "Updated DATAset.csv")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


# ================================================================
#  STEP 1 — LOAD RAW DATASET
# ================================================================
def load_data():
    """
    Reads the Excel file into a DataFrame.
    Expected: 10000 rows × 41 columns
    """
    print("\n" + "="*55)
    print("  SMART WASTE AI — PREPROCESSING PIPELINE")
    print("="*55)
    print(f"\n[STEP 1] Loading dataset ...")
    print(f"         {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    print(f"         ✅ {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


# ================================================================
#  STEP 2 — DROP COLUMNS THAT ADD NO VALUE TO ML
#
#  WHY DROP THESE?
#  Record_ID  → just 1,2,3... row counter. No pattern.
#  Area_ID    → location code. Model can't learn from an ID.
#  Vehicle_ID → vehicle code. Same reason.
#  Road_ID    → road code.    Same reason.
#  These would confuse the model into memorising IDs instead
#  of learning real patterns.
# ================================================================
def drop_columns(df):
    cols = ["Record_ID", "Area_ID", "Vehicle_ID", "Road_ID"]
    df   = df.drop(columns=cols)
    print(f"\n[STEP 2] Dropped {len(cols)} ID columns")
    print(f"         {cols}")
    print(f"         Remaining: {df.shape[1]} columns")
    return df


# ================================================================
#  STEP 3 — FIX NULL VALUES
#
#  ONLY 2 COLUMNS HAVE NULLS:
#  Festival_Event → 7,056 nulls
#    WHY NULL? Most days have no festival. NaN = normal day.
#    FIX: fill with "No_Festival"
#
#  Disaster_Event → 7,743 nulls
#    WHY NULL? Most days have no disaster. NaN = normal day.
#    FIX: fill with "No_Disaster"
#
#  We fill rather than drop rows because dropping 7000+
#  rows would remove 70% of our training data.
# ================================================================
def fill_nulls(df):
    df = df.fillna(0)
    df["Festival_Event"] = df["Festival_Event"].fillna("No_Festival")
    df["Disaster_Event"] = df["Disaster_Event"].fillna("No_Disaster")

    print(f"\n[STEP 3] Null values fixed:")
    print(f"         Festival_Event → filled with 'No_Festival'")
    print(f"         Disaster_Event → filled with 'No_Disaster'")
    print(f"         Total nulls remaining: {df.isnull().sum().sum()}")
    return df


# ================================================================
#  STEP 4 — EXTRACT DATE FEATURES
#
#  WHY?
#  The raw Date column (e.g. "2024-04-12") is a datetime object.
#  ML models cannot directly use dates.
#
#  WHAT WE EXTRACT:
#  month     → 1 to 12
#              captures seasonal patterns
#              (April=4 uses more water than December=12)
#
#  dayofweek → 0=Monday to 6=Sunday
#              captures weekday vs weekend patterns
#              (weekends generate more household waste)
#
#  Then we DROP the original Date column.
# ================================================================
def extract_date_features(df):
    df["Date"]      = pd.to_datetime(df["Date"], dayfirst = True)
    df["month"]     = df["Date"].dt.month
    df["dayofweek"] = df["Date"].dt.dayofweek
    df              = df.drop(columns=["Date"])

    print(f"\n[STEP 4] Date column processed:")
    print(f"         Extracted → 'month' (1-12)")
    print(f"         Extracted → 'dayofweek' (0=Mon, 6=Sun)")
    print(f"         Date column dropped")
    return df


# ================================================================
#  STEP 5 — ENCODE CATEGORICAL (TEXT) COLUMNS
#
#  WHY?
#  ML models only work with numbers. Text columns like
#  "Summer", "Urban", "High" must be converted to integers.
#
#  HOW — LabelEncoder (alphabetical order):
#    Urban_Rural_Type  : Rural=0,  Urban=1
#    Season            : Monsoon=0, Summer=1, Winter=2
#    Day_Type          : Weekday=0, Weekend=1
#    Festival_Event    : Local_Festival=0, National_Festival=1,
#                        No_Festival=2
#    Traffic_Congestion: High=0, Low=1, Medium=2
#    Road_Type         : Highway=0, Main_Road=1, Residential=2
#    Road_Condition    : Average=0, Good=1, Poor=2
#    Disaster_Event    : Cyclone=0, Flood=1, Heatwave=2,
#                        Landslide=3, No_Disaster=4
#
#  WHY SAVE .pkl?
#  The FastAPI backend (main.py) receives live inputs like
#  {"Season": "Summer"} and must convert them using the
#  EXACT SAME encoding used during training.
#  If we create a new encoder, "Summer" might get a different
#  number and predictions would be wrong.
# ================================================================
CATEGORICAL_COLS = [
    "Urban_Rural_Type",
    "Season",
    "Day_Type",
    "Festival_Event",
    "Traffic_Congestion_Level",
    "Road_Type",
    "Road_Condition",
    "Disaster_Event",
]

def encode_categoricals(df):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    encoders = {}
    print(f"\n[STEP 5] Encoding {len(CATEGORICAL_COLS)} text columns to numbers:")
    for col in CATEGORICAL_COLS:
        le            = LabelEncoder()
        df[col]       = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        print(f"         {col:<35} → {list(le.classes_)}")

    # Save all encoders in one file
    # loaded later by decision_logic.py for live requests
    save_path = os.path.join(PROCESSED_DIR, "label_encoders.pkl")
    joblib.dump(encoders, save_path)
    print(f"\n         💾 label_encoders.pkl saved")
    print(f"            → loaded later by decision_logic.py")
    return df, encoders


# ================================================================
#  FEATURE SETS — EACH MODEL USES DIFFERENT COLUMNS
#
#  WHY DIFFERENT FEATURES PER MODEL?
#  Each prediction problem needs different information:
#
#  💧 WATER:  demographic + weather + past water usage
#  🗑️ WASTE:  waste history + composition + collection info
#  🗺️ ROUTE:  vehicle + road + traffic info
#
#  Mixing features across models would add noise and
#  reduce accuracy. Clean separation = better models.
# ================================================================

# ------ 💧 MODEL 1: Water Demand --------------------------------
# Predicts: Water_Demand (litres/day)  range: 60–600
# 16 input features
WATER_FEATURES = [
    "Population",               # more people  → more water needed
    "Temperature_C",            # hot weather → more demand
    "Rainfall_mm",              # rain reduces tap water demand
    "Humidity_percent",         # affects evaporation & consumption
    "Season",                   # Summer = peak water demand
    "Day_Type",                 # weekend patterns differ
]
WATER_TARGET = "Water_Demand"

# ------ 🗑️ MODEL 2: Waste Generation ---------------------------
# Predicts: Waste_Generated_tons (tonnes/day)  range: 25–250
# 19 input features — DIFFERENT from water model
WASTE_FEATURES = [
    "Population",                    # more people → more waste
    "Population_Density",            # density affects waste volume
    "Temperature_C",                 # heat speeds organic decay
    "Rainfall_mm",                   # rain affects collection
    "Season",                        # seasonal waste patterns
    "Day_Type",                      # weekends = more household waste
    "Festival_Event",                # festivals = waste spike
    "Disaster_Event",                # disasters = extra debris
    "Past_Waste_t1_tons",            # yesterday's waste (strongest)
    "Past_Waste_t7_tons",            # last 7-day rolling total
    "Past_Waste_t30_tons",           # last 30-day rolling total
    "Organic_Waste_percent",         # organic % affects total
    "Plastic_Waste_percent",         # plastic % affects total
    "Paper_Waste_percent",           # paper % affects total
    "Other_Waste_percent",           # other % affects total
    "Collection_Frequency_per_week", # more collection = less buildup
    "Recycling_Rate_percent",        # more recycling = less final waste
    "month",                         # monthly trend
    "dayofweek",                     # day of week trend
]
WASTE_TARGET = "Waste_Generated_tons"

# ------ 🗺️ MODEL 3: Route Travel Time -------------------------
# Predicts: Travel_Time_min (minutes)  range: 5–180
# 11 input features — DIFFERENT from both above
# Used by route_optimizer.py to score each road segment
ROUTE_FEATURES = [
    "Distance_km",               # core signal: longer = more time
    "Vehicle_Capacity_kg",       # heavier capacity = slower
    "Current_Load_kg",           # more load = slower on hills
    "Fuel_Consumption_km_per_l", # fuel efficiency relates to speed
    "Traffic_Congestion_Level",  # high traffic = much more time
    "Road_Type",                 # Highway > Main_Road > Residential
    "Road_Condition",            # poor roads = more time
    "One_Way_Flag",              # affects possible routes
    "Toll_Road",                 # toll = likely fast highway
    "Vehicle_Location_Lat",      # geographic location
    "Vehicle_Location_Long",     # geographic location
]
ROUTE_TARGET = "Travel_Time_min"


# ================================================================
#  STEP 6+7+8 — SPLIT, SCALE, SAVE  (runs once per model)
#
#  SPLIT (80/20):
#  80% of rows → training   (model learns from these)
#  20% of rows → testing    (we measure accuracy on these)
#  random_state=42 → same split every time you run
#
#  SCALE (StandardScaler):
#  Converts all numbers to mean=0, std=1
#  WHY: Population=100,000 vs Temperature=35
#       Without scaling, the model would think Population
#       is 3000x more important just because it's bigger.
#  KEY RULE: fit ONLY on train data → transform both
#            (fitting on test = data leakage = fake accuracy)
#
#  SAVE SCALER:
#  When live data comes in via API, we must scale it
#  with the EXACT same scaler used in training.
# ================================================================
def prepare_dataset(df, features, target, name):
    print(f"\n[STEP 6-8] '{name}' model dataset:")
    print(f"           Features  : {len(features)}")
    print(f"           Target    : {target}")

    X = df[features].values
    y = df[target].values

    # 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"           Train     : {X_train.shape[0]:,} rows")
    print(f"           Test      : {X_test.shape[0]:,} rows")

    # Scale: fit on train, transform both
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    # Save scaler for API use
    path = os.path.join(PROCESSED_DIR, f"scaler_{name}.pkl")
    joblib.dump(scaler, path)
    print(f"           💾 scaler_{name}.pkl saved")
    print(f"              → loaded later by decision_logic.py")

    return X_train, X_test, y_train, y_test, scaler


# ================================================================
#  MASTER FUNCTION — called by all 3 training files
#
#  RETURNS:
#  {
#    "water"    : (X_train, X_test, y_train, y_test, scaler),
#    "waste"    : (X_train, X_test, y_train, y_test, scaler),
#    "route"    : (X_train, X_test, y_train, y_test, scaler),
#    "encoders" : { col_name: LabelEncoder },
#    "df"       : full processed DataFrame
#  }
# ================================================================
def run_preprocessing():
    df = load_data()
    df = drop_columns(df)
    df = fill_nulls(df)
    import numpy as np
    df['Water_Demand'] = (
        df['Population'] * 0.0002 +
        df['Temperature_C'] * 15 +
        df['Humidity_percent'] * 5 +
        df['Rainfall_mm'] * 1.5 +
        np.random.normal(0, 80, len(df))
    )
    df = extract_date_features(df)
    df, encoders = encode_categoricals(df)
    print("\n[DATA VALIDATION] Correlation with Water_Demand:\n")
    print(df.corr(numeric_only=True)['Water_Demand'].sort_values(ascending=False))
   
    import matplotlib.pyplot as plt
    plt.scatter(df['Population'], df['Water_Demand'])
    plt.xlabel("Population")
    plt.ylabel("Water Demand")
    plt.title("Population vs Water Demand")
    plt.show()

    water_data = prepare_dataset(df, WATER_FEATURES, WATER_TARGET, "water")
    waste_data = prepare_dataset(df, WASTE_FEATURES, WASTE_TARGET, "waste")
    route_data = prepare_dataset(df, ROUTE_FEATURES, ROUTE_TARGET, "route")

    print(f"\n{'='*55}")
    print(f"  ✅ ALL PREPROCESSING DONE")
    print(f"  📁 Files saved in: {PROCESSED_DIR}")
    print(f"{'='*55}\n")

    return {
        "water"    : water_data,
        "waste"    : waste_data,
        "route"    : route_data,
        "encoders" : encoders,
        "df"       : df,
    }


# ================================================================
#  RUN DIRECTLY TO TEST:
#  python src/data_processing/preprocess.py
# ================================================================
if __name__ == "__main__":
    run_preprocessing()