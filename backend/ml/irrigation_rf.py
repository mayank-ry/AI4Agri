import numpy as np
import pandas as pd
import joblib
import os
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "irrigation_model.pkl"
ENCODER_CROP_PATH = MODEL_DIR / "le_crop.pkl"
ENCODER_STAGE_PATH = MODEL_DIR / "le_stage.pkl"

CROPS = ['wheat', 'rice', 'cotton', 'maize', 'sugarcane', 'soybean']
STAGES = ['seedling', 'vegetative', 'flowering', 'maturity']

WATER_NEED = {  # liters/hectare/day base
    'wheat':  {'seedling': 150, 'vegetative': 300, 'flowering': 500, 'maturity': 150},
    'rice':   {'seedling': 400, 'vegetative': 600, 'flowering': 700, 'maturity': 300},
    'cotton': {'seedling': 200, 'vegetative': 400, 'flowering': 600, 'maturity': 200},
    'maize':  {'seedling': 200, 'vegetative': 350, 'flowering': 500, 'maturity': 200},
    'sugarcane': {'seedling': 300, 'vegetative': 500, 'flowering': 650, 'maturity': 250},
    'soybean': {'seedling': 180, 'vegetative': 320, 'flowering': 480, 'maturity': 180},
}

def _generate_data(n=8000) -> pd.DataFrame:
    np.random.seed(42)
    data = {
        'soil_moisture': np.random.uniform(10, 80, n),
        'temp': np.random.uniform(15, 45, n),
        'humidity': np.random.uniform(20, 90, n),
        'crop': np.random.choice(CROPS, n),
        'stage': np.random.choice(STAGES, n),
        'days_since_irrigation': np.random.randint(0, 30, n),
        'et0': np.random.uniform(1, 10, n),
        'rainfall_48h': np.random.uniform(0, 50, n),
        'wind_speed': np.random.uniform(0, 20, n)
    }
    
    df = pd.DataFrame(data)
    water_needed = []
    
    for _, row in df.iterrows():
        base_water = WATER_NEED[row['crop']][row['stage']]
        
        # Domain logic adjustments
        if row['rainfall_48h'] > 15:
            needed = 0
        elif row['soil_moisture'] > 60:
            needed = 0
        else:
            # Adjust based on ET0 and Temp
            et0_adj = row['et0'] / 5.0
            temp_adj = row['temp'] / 25.0
            moisture_deficit = max(0, 60 - row['soil_moisture']) / 60.0
            
            needed = base_water * et0_adj * temp_adj * (1 + moisture_deficit)
            # Days since irrigation factor
            if row['days_since_irrigation'] > 10:
                needed *= 1.2
            elif row['days_since_irrigation'] == 0:
                needed = 0
                
        # Add slight noise
        needed += np.random.normal(0, needed * 0.05) if needed > 0 else 0
        water_needed.append(max(0, needed))
        
    df['water_needed_liters_ha'] = water_needed
    return df

def _train_model():
    print("Training Irrigation RandomForest Model...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    df = _generate_data(8000)
    
    le_crop = LabelEncoder()
    le_stage = LabelEncoder()
    
    df['crop_encoded'] = le_crop.fit_transform(df['crop'])
    df['stage_encoded'] = le_stage.fit_transform(df['stage'])
    
    X = df[['soil_moisture', 'temp', 'humidity', 'crop_encoded', 'stage_encoded', 
            'days_since_irrigation', 'et0', 'rainfall_48h', 'wind_speed']]
    y = df['water_needed_liters_ha']
    
    model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le_crop, ENCODER_CROP_PATH)
    joblib.dump(le_stage, ENCODER_STAGE_PATH)
    
    print("Irrigation Model training complete and saved.")

def load_model():
    if not (os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_CROP_PATH) and os.path.exists(ENCODER_STAGE_PATH)):
        _train_model()
        
    model = joblib.load(MODEL_PATH)
    le_crop = joblib.load(ENCODER_CROP_PATH)
    le_stage = joblib.load(ENCODER_STAGE_PATH)
    return model, le_crop, le_stage

_model, _le_crop, _le_stage = None, None, None

def predict_irrigation(soil_moisture: float, temp: float,
                       humidity: float, crop: str,
                       stage: str, days_since_water: int,
                       et0: float, rain_48h: float,
                       wind_speed: float = 10) -> dict:
    global _model, _le_crop, _le_stage
    
    if _model is None:
        _model, _le_crop, _le_stage = load_model()
        
    crop_lower = crop.lower()
    stage_lower = stage.lower()
    
    # Fallbacks if unknown
    if crop_lower not in CROPS: crop_lower = 'wheat'
    if stage_lower not in STAGES: stage_lower = 'vegetative'
        
    crop_enc = _le_crop.transform([crop_lower])[0]
    stage_enc = _le_stage.transform([stage_lower])[0]
    
    X_pred = pd.DataFrame([{
        'soil_moisture': soil_moisture,
        'temp': temp,
        'humidity': humidity,
        'crop_encoded': crop_enc,
        'stage_encoded': stage_enc,
        'days_since_irrigation': days_since_water,
        'et0': et0,
        'rainfall_48h': rain_48h,
        'wind_speed': wind_speed
    }])
    
    predicted_water = float(_model.predict(X_pred)[0])
    
    # Determine urgency
    urgency = 1
    if predicted_water > 800: urgency = 10
    elif predicted_water > 500: urgency = 7
    elif predicted_water > 200: urgency = 4
    
    # Generate 7-day schedule
    schedule = []
    if predicted_water > 0:
        schedule.append({"day": 1, "action": "Irrigate", "liters": round(predicted_water, 0)})
        schedule.append({"day": 4, "action": "Check Moisture", "liters": 0})
    else:
        schedule.append({"day": 3, "action": "Check Moisture", "liters": 0})
        
    method_hi = "Drip irrigation (Tapkan vidhi) ka upyog karein" if predicted_water < 600 else "Flood irrigation (Pravah vidhi) ya Sprinkler ka upyog karein"
    
    return {
        "water_liters_ha": round(predicted_water, 0),
        "urgency": urgency,
        "schedule_7_days": schedule,
        "method_hi": method_hi
    }
