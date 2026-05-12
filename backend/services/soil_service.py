import httpx
import structlog

log = structlog.get_logger()
BASE_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

async def get_soil_data(lat: float, lon: float) -> dict:
    try:
        params = {
            "lon": lon, 
            "lat": lat,
            "property": ["phh2o", "soc", "nitrogen", "clay", "sand", "wv0010"],
            "depth": "0-5cm",
            "value": "mean"
        }
        
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(BASE_URL, params=params)
            r.raise_for_status()
            data = r.json()
       
        props = data.get('properties', {}).get('layers', [])
        result = _parse_soilgrids(props)
        return result
    except Exception as e:
        log.error("SoilGrids failed", error=str(e))
        return _default_soil()

def _parse_soilgrids(layers: list) -> dict:
    soil = {}
    for layer in layers:
        name = layer.get('name', '')
        value = None
        try:
            value = layer['depths'][0]['values']['mean']
        except Exception:
            pass
            
        if name == 'phh2o' and value is not None:
            soil['ph'] = round(value / 10.0, 2)  # SoilGrids pH * 10
        elif name == 'nitrogen' and value is not None:
            soil['nitrogen_mg_kg'] = round(value / 100.0, 1)
        elif name == 'soc' and value is not None:
            soil['organic_carbon'] = round(value / 10.0, 2)
        elif name == 'wv0010' and value is not None:
            soil['moisture_pct'] = round(value / 10.0, 1)
            
    # Set defaults for missing
    soil.setdefault('ph', 6.8)
    soil.setdefault('nitrogen_mg_kg', 150.0)
    soil.setdefault('phosphorus_mg_kg', 45.0)
    soil.setdefault('potassium_mg_kg', 180.0)
    soil.setdefault('moisture_pct', 45.0)
    soil.setdefault('organic_carbon', 1.2)
    soil['field_capacity'] = 0.35
    soil['wilting_point'] = 0.15
    return soil

def _default_soil() -> dict:
    return {
        'ph': 6.8,
        'nitrogen_mg_kg': 150.0,
        'phosphorus_mg_kg': 45.0,
        'potassium_mg_kg': 180.0,
        'moisture_pct': 45.0,
        'organic_carbon': 1.2,
        'field_capacity': 0.35,
        'wilting_point': 0.15
    }
