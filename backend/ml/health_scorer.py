import numpy as np
from datetime import date

CROP_TOTAL_DAYS = {
    'wheat': 150, 'rice': 135, 'cotton': 180,
    'maize': 120, 'sugarcane': 365, 'soybean': 100
}

CROP_KC = {
    'wheat':     {'initial': 0.30, 'development': 0.75, 'mid': 1.15, 'late': 0.40},
    'rice':      {'initial': 1.05, 'development': 1.10, 'mid': 1.20, 'late': 0.90},
    'cotton':    {'initial': 0.35, 'development': 0.75, 'mid': 1.15, 'late': 0.70},
    'maize':     {'initial': 0.30, 'development': 0.70, 'mid': 1.20, 'late': 0.35},
    'sugarcane': {'initial': 0.40, 'development': 0.80, 'mid': 1.25, 'late': 0.75},
    'soybean':   {'initial': 0.40, 'development': 0.80, 'mid': 1.15, 'late': 0.50},
}

YIELD_POTENTIAL = {
    'wheat': 4.5, 'rice': 4.0, 'cotton': 2.2,
    'maize': 3.5, 'sugarcane': 70.0, 'soybean': 1.5
}

def get_growth_stage_normalized(sowing_date: date, crop_type: str) -> float:
    crop = crop_type.lower()
    total_days = CROP_TOTAL_DAYS.get(crop, 120)  # Default 120 days
    days_passed = (date.today() - sowing_date).days
    
    # Clamp between 0.0 and 1.0
    return float(np.clip(days_passed / total_days, 0.0, 1.0))

def get_kc(crop_type: str, stage_normalized: float) -> float:
    crop = crop_type.lower()
    if crop not in CROP_KC:
        crop = 'wheat' # Fallback
        
    stages = CROP_KC[crop]
    if stage_normalized <= 0.2:
        return stages['initial']
    elif stage_normalized <= 0.5:
        return stages['development']
    elif stage_normalized <= 0.8:
        return stages['mid']
    else:
        return stages['late']

def get_adaptive_weights(t: float) -> dict:
    weights = {
        'ndvi':     0.20 + 0.30 * np.exp(-8 * (t - 0.5)**2),
        'moisture': 0.35 * np.exp(-2 * t) + 0.10,
        'temp':     0.10 + 0.20 * t,
        'nutrient': 0.25 * np.exp(-3 * (t - 0.3)**2) + 0.08,
        'ph':       0.08 * (1 - 0.3 * t),
    }
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}

def phenological_penalty(ndvi: float, t: float) -> float:
    expected = 0.85 * np.exp(-6 * (t - 0.55)**2) + 0.15
    return float(np.exp(-5 * abs(ndvi - expected)))

def seasonal_stress(temp: float, humidity: float) -> float:
    # Vapor Pressure Deficit (VPD) based
    vpd = (1 - humidity / 100.0) * 0.6108 * np.exp(17.27 * temp / (temp + 237.3))
    return float(1.0 - min(vpd / 4.0, 0.4))

def calculate_achs(ndvi: float, moisture: float, temp: float,
                   humidity: float, ph: float,
                   nitrogen: float, sowing_date: date,
                   crop_type: str) -> dict:
    t = get_growth_stage_normalized(sowing_date, crop_type)
    w = get_adaptive_weights(t)
    
    signals = {
        'ndvi':     float(np.clip((ndvi - 0.1) / 0.7, 0, 1)),
        'moisture': float(np.clip(moisture / 100.0, 0, 1)),
        'temp':     float(np.clip(1 - abs(temp - 22) / 25.0, 0, 1)),
        'nutrient': float(np.clip(nitrogen / 200.0, 0, 1)),
        'ph':       float(np.clip(1 - abs(ph - 6.5) / 3.0, 0, 1)),
    }
    
    base = sum(w[k] * signals[k] for k in w) * 100
    P = phenological_penalty(ndvi, t)
    S = seasonal_stress(temp, humidity)
    achs = base * P * S
    
    status = ("Excellent" if achs >= 75 else "Good" if achs >= 55
              else "Fair" if achs >= 35 else "Poor")
    status_hi = ("Bahut Achha" if achs >= 75 else "Achha"
                 if achs >= 55 else "Theek" if achs >= 35
                 else "Kharab")
                 
    return {
        'achs_score': round(achs, 1),
        'status': status,
        'status_hi': status_hi,
        'component_scores': signals,
        'weights_used': w,
        'phenological_fit': round(P, 4),
        'stress_multiplier': round(S, 4),
        'growth_stage_t': round(t, 3),
    }

def calculate_wsri(et0: float, kc: float, rainfall_mm: float,
                   soil_moisture: float,
                   field_capacity: float = 0.35,
                   wilting_point: float = 0.15) -> dict:
    etc = et0 * kc
    pe = rainfall_mm * 0.75
    taw = 1000 * (field_capacity - wilting_point)
    raw = 0.5 * taw
    dr = max(0, field_capacity - soil_moisture / 100.0)
    
    ks = 1.0 if dr <= raw else max(0, (taw - dr) / (taw - raw))
    nir = max(0, etc - pe)
    
    wsri = min(100.0, (nir / max(etc, 0.1)) * ks * 100)
    
    priority = ("CRITICAL" if wsri > 75 else "HIGH" if wsri > 50
                else "MEDIUM" if wsri > 25 else "LOW")
                
    water_liters_ha = round(nir * 10000, 0)  # mm to L/ha
    
    reason_hi = {
        'CRITICAL': 'Khet bahut sukha hai, turant paani den!',
        'HIGH': 'Fasal ko paani ki zarurat hai.',
        'MEDIUM': 'Agale 2 din mein paani dein.',
        'LOW': 'Abhi paani dene ki zarurat nahi.',
    }[priority]
    
    return {
        'wsri_score': round(wsri, 1),
        'etc_mm': round(etc, 3),
        'nir_mm': round(nir, 3),
        'stress_coeff_ks': round(ks, 4),
        'priority': priority,
        'water_liters_ha': water_liters_ha,
        'reason_hi': reason_hi,
    }

def calculate_cyas(crop: str, ndvi: float,
                   wsri: float, nitrogen: float,
                   temp_avg: float, ph: float) -> dict:
    crop = crop.lower()
    Yp = YIELD_POTENTIAL.get(crop, 3.0)
    
    sensitivity = {
        'ndvi': 0.8, 'water': 0.9, 'nitrogen': 0.7,
        'temp': 0.6, 'ph': 0.4
    }
    
    D = {
        'ndvi':     max(0, (0.75 - ndvi) / 0.75),
        'water':    wsri / 100.0,
        'nitrogen': max(0, (200 - nitrogen) / 200.0),
        'temp':     min(abs(temp_avg - 22) / 20.0, 1.0),
        'ph':       min(abs(ph - 6.5) / 3.0, 1.0),
    }
    
    penalty = 1.0
    for f, d in D.items():
        penalty *= (1 - sensitivity[f] * d**2)
        
    predicted = round(Yp * max(penalty, 0.1), 2)
    achievement = round((predicted / Yp) * 100, 1)
    
    limiting = max(D, key=D.get)
    limiting_hi = {
        'ndvi': 'Satellite data (fasal ki sehat)',
        'water': 'Paani ki kami',
        'nitrogen': 'Nitrogen ki kami',
        'temp': 'Tapmaan (garmi/thandi)',
        'ph': 'Mitti ka pH',
    }[limiting]
    
    tips_hi = []
    if D['water'] > 0.3:
        tips_hi.append('Sinchai schedule follow karein')
    if D['nitrogen'] > 0.3:
        tips_hi.append('Urea/DAP khad daalen')
    if D['ndvi'] > 0.3:    
        tips_hi.append('Fasal ki sehat improve karein')
        
    return {
        'predicted_yield': predicted,
        'potential_yield': Yp,
        'achievement_pct': achievement,
        'limiting_factor_hi': limiting_hi,
        'improvement_tips_hi': tips_hi or ['Fasal ki dekhbhal jaari rakhen'],
    }
