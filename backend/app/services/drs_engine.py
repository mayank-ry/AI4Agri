from typing import Dict, Any, List
from app.schemas.drs import DRSResult, DRSConditionFactor

# Config-driven crop thresholds
CROP_THRESHOLDS = {
    "wheat": {
        "temp_min": 15.0,
        "temp_max": 25.0,
        "rainfall_3d_threshold": 20.0,  # mm
    },
    "rice": {
        "temp_min": 20.0,
        "temp_max": 30.0,
        "rainfall_3d_threshold": 50.0,
    },
    "corn": {
        "temp_min": 18.0,
        "temp_max": 27.0,
        "rainfall_3d_threshold": 25.0,
    },
    "default": {
        "temp_min": 15.0,
        "temp_max": 30.0,
        "rainfall_3d_threshold": 30.0,
    }
}

class DRSEngine:
    """
    Disease Risk Score (DRS) Engine - MVP Rule-Based System
    """
    
    WEIGHTS = {
        "high_humidity": 4.0,
        "temp_range": 3.0,
        "high_rainfall": 3.0
    }

    @staticmethod
    def _get_crop_thresholds(crop_type: str) -> Dict[str, float]:
        crop_lower = crop_type.lower()
        return CROP_THRESHOLDS.get(crop_lower, CROP_THRESHOLDS["default"])

    @classmethod
    def calculate_drs(
        cls, 
        crop_type: str, 
        current_humidity: float, 
        current_temp: float, 
        rainfall_3d_total: float
    ) -> DRSResult:
        """
        Calculate the Disease Risk Score (DRS) based on environmental factors.
        Formula: DRS = 100 * (Σ weight_i * met_i) / Σ weight_i
        """
        thresholds = cls._get_crop_thresholds(crop_type)
        
        conditions_met = []
        factors: List[DRSConditionFactor] = []
        reasons: List[str] = []
        
        # Condition 1: Humidity > 80%
        met_humidity = current_humidity > 80.0
        factors.append(DRSConditionFactor(
            name="High Humidity",
            weight=cls.WEIGHTS["high_humidity"],
            met=met_humidity,
            description="Humidity > 80% significantly increases fungal growth risk."
        ))
        if met_humidity:
            conditions_met.append(cls.WEIGHTS["high_humidity"])
            reasons.append(f"Current humidity is critically high ({current_humidity}%).")

        # Condition 2: Temperature in crop-specific danger zone
        temp_min = thresholds["temp_min"]
        temp_max = thresholds["temp_max"]
        met_temp = temp_min <= current_temp <= temp_max
        factors.append(DRSConditionFactor(
            name="Optimal Disease Temp",
            weight=cls.WEIGHTS["temp_range"],
            met=met_temp,
            description=f"Temperature is within the optimal growth range for pathogens ({temp_min}-{temp_max}°C)."
        ))
        if met_temp:
            conditions_met.append(cls.WEIGHTS["temp_range"])
            reasons.append(f"Temperature ({current_temp}°C) is in the danger zone for {crop_type}.")

        # Condition 3: Rainfall threshold exceeded in last 3 days
        rain_threshold = thresholds["rainfall_3d_threshold"]
        met_rain = rainfall_3d_total >= rain_threshold
        factors.append(DRSConditionFactor(
            name="Recent Heavy Rainfall",
            weight=cls.WEIGHTS["high_rainfall"],
            met=met_rain,
            description=f"Accumulated rainfall over 3 days exceeds {rain_threshold}mm, creating prolonged leaf wetness."
        ))
        if met_rain:
            conditions_met.append(cls.WEIGHTS["high_rainfall"])
            reasons.append(f"Heavy rainfall detected in the last 72 hours ({rainfall_3d_total}mm).")

        # Calculate Score
        total_weight = sum(cls.WEIGHTS.values())
        achieved_weight = sum(conditions_met)
        
        raw_score = 100.0 * (achieved_weight / total_weight)
        
        # Determine Risk Level
        if raw_score >= 70:
            risk_level = "High"
        elif raw_score >= 40:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        if raw_score == 0:
            reasons.append("Environmental conditions are currently unfavorable for disease development.")

        return DRSResult(
            score=round(raw_score, 1),
            risk_level=risk_level,
            reasons=reasons,
            factors=factors
        )
