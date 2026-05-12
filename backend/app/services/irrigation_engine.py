from typing import List, Dict, Any
from app.schemas.irrigation import IrrigationRecommendationResult, IrrigationFactor

# Configurable Weights & Factors
CONFIG = {
    "ndvi_min_crop": 0.2,
    "ndvi_max_crop": 0.8,
    "wsi_weights": {
        "soil_moisture": 0.7,
        "temperature_stress": 0.3
    },
    "soil_factors": {
        "sandy": 1.2,   # Loses water fast
        "loam": 1.0,    # Baseline
        "clay": 0.8     # Retains water well
    },
    "crop_stages": {
        "germination": 1.1,
        "vegetative": 1.0,
        "flowering": 1.5,   # Critical
        "fruiting": 1.3,
        "maturity": 0.5     # Minimal water needed
    },
    "base_irrigation_mm": 15.0
}

class IrrigationEngine:
    @staticmethod
    def normalize_ndvi(ndvi: float) -> float:
        """Normalize NDVI (typically -1 to 1) to a 0-1 scale for crop health."""
        min_n = CONFIG["ndvi_min_crop"]
        max_n = CONFIG["ndvi_max_crop"]
        if ndvi < min_n:
            return 0.0
        if ndvi > max_n:
            return 1.0
        return (ndvi - min_n) / (max_n - min_n)

    @classmethod
    def calculate_fhs(cls, ndvi: float) -> float:
        """Field Health Score (FHS) from 0 to 100 based on NDVI."""
        return round(cls.normalize_ndvi(ndvi) * 100.0, 1)

    @classmethod
    def calculate_wsi(cls, soil_moisture_pct: float, current_temp: float, optimal_temp: float = 25.0) -> float:
        """
        Water Stress Index (WSI) from 0 to 100.
        Combines inverse soil moisture and temperature deviation.
        """
        moisture_stress = max(0.0, 100.0 - soil_moisture_pct)
        
        # Temp stress increases if temp is significantly higher than optimal
        temp_stress = max(0.0, min(100.0, (current_temp - optimal_temp) * 5.0))
        
        w_sm = CONFIG["wsi_weights"]["soil_moisture"]
        w_t = CONFIG["wsi_weights"]["temperature_stress"]
        
        wsi = (moisture_stress * w_sm) + (temp_stress * w_t)
        return round(wsi, 1)

    @classmethod
    def generate_recommendation(
        cls,
        ndvi: float,
        soil_moisture_pct: float,
        current_temp: float,
        soil_type: str,
        crop_stage: str,
        forecasted_rain_mm: float
    ) -> IrrigationRecommendationResult:
        factors: List[IrrigationFactor] = []
        reasons: List[str] = []
        
        # 1. Base Metrics
        fhs = cls.calculate_fhs(ndvi)
        wsi = cls.calculate_wsi(soil_moisture_pct, current_temp)
        
        factors.append(IrrigationFactor(
            name="Water Stress Index (WSI)",
            value=wsi,
            impact="increase" if wsi > 50 else "neutral",
            description=f"Current water stress level is {wsi}/100 based on soil moisture and temperature."
        ))
        
        # 2. Modifiers
        soil_factor = CONFIG["soil_factors"].get(soil_type.lower(), 1.0)
        stage_factor = CONFIG["crop_stages"].get(crop_stage.lower(), 1.0)
        
        factors.append(IrrigationFactor(
            name="Soil Type Retention",
            value=soil_factor,
            impact="increase" if soil_factor > 1.0 else "decrease",
            description=f"{soil_type.capitalize()} soil modifies water requirement by {soil_factor}x."
        ))
        
        factors.append(IrrigationFactor(
            name="Crop Stage Criticality",
            value=stage_factor,
            impact="increase" if stage_factor > 1.0 else "decrease",
            description=f"The {crop_stage} stage modifies water necessity by {stage_factor}x."
        ))

        # 3. Irrigation Priority Index (IPI)
        # IPI scales the base WSI with the modifiers, reducing by forecasted rain
        base_ipi = wsi * soil_factor * stage_factor
        rain_reduction = min(base_ipi, forecasted_rain_mm * 2.0) # Assume 1mm rain reduces IPI by 2 points
        ipi = max(0.0, base_ipi - rain_reduction)
        ipi = min(100.0, round(ipi, 1))
        
        if forecasted_rain_mm > 0:
            factors.append(IrrigationFactor(
                name="Rain Forecast Offset",
                value=-rain_reduction,
                impact="decrease",
                description=f"Forecasted {forecasted_rain_mm}mm rain reduces priority."
            ))

        # 4. Determine Action
        irrigation_required = ipi >= 40.0
        recommended_amount_mm = 0.0
        
        if irrigation_required:
            reasons.append("Irrigation priority index exceeds the critical threshold of 40.")
            # Calculate amount
            recommended_amount_mm = round((ipi / 100.0) * CONFIG["base_irrigation_mm"] * soil_factor * stage_factor, 1)
            
            # Reduce recommended amount strictly by forecasted rain
            recommended_amount_mm = max(0.0, recommended_amount_mm - forecasted_rain_mm)
            if recommended_amount_mm == 0:
                irrigation_required = False
                reasons.append("Forecasted rainfall entirely covers the crop's water requirements. Irrigation skipped.")
            else:
                reasons.append(f"Applying {recommended_amount_mm}mm is recommended for {soil_type} soil during the {crop_stage} stage.")
        else:
            if wsi < 30:
                reasons.append("Soil moisture levels are currently adequate.")
            elif forecasted_rain_mm > 10:
                reasons.append("Impending rainfall is sufficient to cover crop needs.")
            else:
                reasons.append("Crop is in a low-water requirement stage or conditions are stable.")

        return IrrigationRecommendationResult(
            irrigation_required=irrigation_required,
            recommended_amount_mm=recommended_amount_mm,
            priority_index=ipi,
            fhs=fhs,
            wsi=wsi,
            reasons=reasons,
            factors=factors
        )
