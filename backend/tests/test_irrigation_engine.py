from ml.irrigation_engine import IrrigationEngine

def test_irrigation_not_required():
    result = IrrigationEngine.generate_recommendation(
        ndvi=0.7,
        soil_moisture_pct=80.0,  # High moisture
        current_temp=22.0,       # Cool
        soil_type="clay",        # High retention
        crop_stage="vegetative",
        forecasted_rain_mm=5.0   # Some rain
    )
    assert result.irrigation_required is False
    assert result.priority_index < 40.0
    assert result.recommended_amount_mm == 0.0

def test_irrigation_highly_required():
    result = IrrigationEngine.generate_recommendation(
        ndvi=0.6,
        soil_moisture_pct=20.0,  # Very dry
        current_temp=35.0,       # Very hot
        soil_type="sandy",       # Low retention (1.2)
        crop_stage="flowering",  # Critical (1.5)
        forecasted_rain_mm=0.0
    )
    assert result.wsi > 70.0
    assert result.irrigation_required is True
    assert result.priority_index > 80.0
    assert result.recommended_amount_mm > 10.0
    assert len(result.reasons) > 0

def test_rain_forecast_cancels_irrigation():
    result = IrrigationEngine.generate_recommendation(
        ndvi=0.6,
        soil_moisture_pct=40.0,  # Dry
        current_temp=30.0,
        soil_type="loam",
        crop_stage="vegetative",
        forecasted_rain_mm=25.0  # Massive rain coming
    )
    # The WSI is high enough to trigger base priority, but rain nullifies it
    assert result.irrigation_required is False
    assert result.recommended_amount_mm == 0.0
    assert any("rainfall" in r.lower() for r in result.reasons)
