import pytest
from app.services.drs_engine import DRSEngine

def test_drs_low_risk():
    result = DRSEngine.calculate_drs(
        crop_type="wheat",
        current_humidity=50.0,  # Below 80
        current_temp=10.0,      # Below 15
        rainfall_3d_total=5.0   # Below 20
    )
    assert result.score == 0.0
    assert result.risk_level == "Low"
    assert len(result.reasons) == 1
    assert "unfavorable" in result.reasons[0]
    assert len(result.factors) == 3
    assert not any(f.met for f in result.factors)

def test_drs_high_risk_wheat():
    result = DRSEngine.calculate_drs(
        crop_type="wheat",
        current_humidity=85.0,  # Met (Weight 4)
        current_temp=20.0,      # Met (Weight 3)
        rainfall_3d_total=25.0  # Met (Weight 3)
    )
    assert result.score == 100.0
    assert result.risk_level == "High"
    assert len(result.reasons) == 3
    assert all(f.met for f in result.factors)

def test_drs_medium_risk_rice():
    # Only temperature matches
    result = DRSEngine.calculate_drs(
        crop_type="rice",
        current_humidity=70.0,  # Not Met
        current_temp=25.0,      # Met (Weight 3)
        rainfall_3d_total=10.0  # Not Met
    )
    # Total weight = 10, Achieved = 3
    assert result.score == 30.0
    assert result.risk_level == "Low"

    # Humidity and temp matches
    result_med = DRSEngine.calculate_drs(
        crop_type="rice",
        current_humidity=85.0,  # Met (Weight 4)
        current_temp=25.0,      # Met (Weight 3)
        rainfall_3d_total=10.0  # Not Met
    )
    # Total weight = 10, Achieved = 7
    assert result_med.score == 70.0
    assert result_med.risk_level == "High"
