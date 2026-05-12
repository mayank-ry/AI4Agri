# Mathematical Indices

## Disease Risk Score (DRS)

The Disease Risk Score is a deterministic, rule-based algorithm designed to estimate the probability of fungal or bacterial disease outbreak in a field based on immediate micro-climate data. 

**Formula:**
`DRS = 100 * (Σ condition_weight_i * condition_met_i) / Σ condition_weight_i`

Where `condition_met_i` is a binary `1` (True) or `0` (False).

**Current Conditions Evaluated:**
1. **Humidity Threshold**: Relative humidity > 80% (Weight: 4.0)
2. **Temperature Range**: Current temperature falls within the optimal pathogen growth range for the specific crop type (Weight: 3.0)
3. **Accumulated Rainfall**: Total rainfall over the previous 72 hours exceeds the crop-specific tolerance (Weight: 3.0)

**Explainability (`factors` & `reasons`):**
The DRS engine does not act as a black-box. Every calculation returns a breakdown of exactly which factors triggered, empowering the farmer to make localized decisions (e.g., applying fungicide because the 3-day rainfall was unusually high).

## Irrigation Metrics

### Normalized NDVI
NDVI (Normalized Difference Vegetation Index) ranges from -1 to +1. For agricultural analysis, we scale it to `[0, 1]` based on empirical crop limits.
**Formula:** `Normalized_NDVI = max(0, min(1, (NDVI - 0.2) / (0.8 - 0.2)))`

### Field Health Score (FHS)
A 0-100 representation of the crop's vigor.
**Formula:** `FHS = Normalized_NDVI * 100`

### Water Stress Index (WSI)
Estimates physical water stress using soil moisture and extreme temperatures.
**Formula:** `WSI = (0.7 * (100 - Soil_Moisture_%)) + (0.3 * Temp_Stress_Modifier)`

### Irrigation Priority Index (IPI)
A unified 0-100 score prioritizing which fields need immediate watering.
**Formula:** `IPI = (WSI * Soil_Retention_Factor * Crop_Stage_Factor) - (Forecasted_Rain_mm * Rain_Weight)`
Fields with an `IPI >= 40` trigger `irrigation_required = True`.
