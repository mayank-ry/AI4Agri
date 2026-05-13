from typing import List

from pydantic import BaseModel


class IrrigationFactor(BaseModel):
    name: str
    value: float
    impact: str
    description: str


class IrrigationRecommendationResult(BaseModel):
    irrigation_required: bool
    recommended_amount_mm: float
    priority_index: float
    fhs: float
    wsi: float
    reasons: List[str]
    factors: List[IrrigationFactor]


CONFIG = {
    "ndvi_min_crop": 0.2,
    "ndvi_max_crop": 0.8,
    "wsi_weights": {
        "soil_moisture": 0.7,
        "temperature_stress": 0.3,
    },
    "soil_factors": {
        "sandy": 1.2,
        "loam": 1.0,
        "clay": 0.8,
    },
    "crop_stages": {
        "germination": 1.1,
        "vegetative": 1.0,
        "flowering": 1.5,
        "fruiting": 1.3,
        "maturity": 0.5,
    },
    "base_irrigation_mm": 15.0,
}


class IrrigationEngine:
    @staticmethod
    def normalize_ndvi(ndvi: float) -> float:
        min_n = CONFIG["ndvi_min_crop"]
        max_n = CONFIG["ndvi_max_crop"]
        if ndvi < min_n:
            return 0.0
        if ndvi > max_n:
            return 1.0
        return (ndvi - min_n) / (max_n - min_n)

    @classmethod
    def calculate_fhs(cls, ndvi: float) -> float:
        return round(cls.normalize_ndvi(ndvi) * 100.0, 1)

    @classmethod
    def calculate_wsi(cls, soil_moisture_pct: float, current_temp: float, optimal_temp: float = 25.0) -> float:
        moisture_stress = max(0.0, 100.0 - soil_moisture_pct)
        temp_stress = max(0.0, min(100.0, (current_temp - optimal_temp) * 5.0))
        weights = CONFIG["wsi_weights"]
        return round((moisture_stress * weights["soil_moisture"]) + (temp_stress * weights["temperature_stress"]), 1)

    @classmethod
    def generate_recommendation(
        cls,
        ndvi: float,
        soil_moisture_pct: float,
        current_temp: float,
        soil_type: str,
        crop_stage: str,
        forecasted_rain_mm: float,
    ) -> IrrigationRecommendationResult:
        factors: List[IrrigationFactor] = []
        reasons: List[str] = []

        fhs = cls.calculate_fhs(ndvi)
        wsi = cls.calculate_wsi(soil_moisture_pct, current_temp)

        factors.append(IrrigationFactor(
            name="Water Stress Index (WSI)",
            value=wsi,
            impact="increase" if wsi > 50 else "neutral",
            description=f"Current water stress level is {wsi}/100 based on soil moisture and temperature.",
        ))

        soil_factor = CONFIG["soil_factors"].get(soil_type.lower(), 1.0)
        stage_factor = CONFIG["crop_stages"].get(crop_stage.lower(), 1.0)

        factors.append(IrrigationFactor(
            name="Soil Type Retention",
            value=soil_factor,
            impact="increase" if soil_factor > 1.0 else "decrease",
            description=f"{soil_type.capitalize()} soil modifies water requirement by {soil_factor}x.",
        ))
        factors.append(IrrigationFactor(
            name="Crop Stage Criticality",
            value=stage_factor,
            impact="increase" if stage_factor > 1.0 else "decrease",
            description=f"The {crop_stage} stage modifies water necessity by {stage_factor}x.",
        ))

        base_ipi = wsi * soil_factor * stage_factor
        rain_reduction = min(base_ipi, forecasted_rain_mm * 2.0)
        ipi = min(100.0, round(max(0.0, base_ipi - rain_reduction), 1))

        if forecasted_rain_mm > 0:
            factors.append(IrrigationFactor(
                name="Rain Forecast Offset",
                value=-rain_reduction,
                impact="decrease",
                description=f"Forecasted {forecasted_rain_mm}mm rain reduces priority.",
            ))

        irrigation_required = ipi >= 40.0
        recommended_amount_mm = 0.0

        if irrigation_required:
            reasons.append("Irrigation priority index exceeds the critical threshold of 40.")
            recommended_amount_mm = round((ipi / 100.0) * CONFIG["base_irrigation_mm"] * soil_factor * stage_factor, 1)
            recommended_amount_mm = max(0.0, recommended_amount_mm - forecasted_rain_mm)
            if recommended_amount_mm == 0:
                irrigation_required = False
                reasons.append("Forecasted rainfall entirely covers the crop's water requirements. Irrigation skipped.")
            else:
                reasons.append(f"Applying {recommended_amount_mm}mm is recommended for {soil_type} soil during the {crop_stage} stage.")
        elif wsi < 30:
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
            factors=factors,
        )
