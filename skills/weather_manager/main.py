import logging
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from agent.tools import ziva_tool

logger = logging.getLogger("SkillWeather")

@ziva_tool
def get_weather(location: str = None, days: int = 7) -> str:
    """
    Obtém previsão do tempo usando Open-Meteo API.

    Args:
        location: Nome da cidade ou coordenadas (ex: "São Paulo" ou "lat,lon")
        days: Número de dias de previsão (1-16, default 7)

    Returns:
        str: Previsão do tempo formatada
    """
    if not location:
        return "Para fornecer a previsão do tempo, preciso que você informe de qual cidade ou local deseja saber."

    try:
        # 1. Geocoding
        if ',' in location and location.replace(',', '').replace('.', '').replace('-', '').isdigit():
            lat, lon = map(float, location.split(','))
            city_name = f"Lat {lat}, Lon {lon}"
        else:
            geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_params = {"name": location, "count": 1, "language": "pt", "format": "json"}
            geo_resp = requests.get(geocode_url, params=geo_params, timeout=10)
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                return json.dumps({"error": f"Localização '{location}' não encontrada."})

            result = geo_data["results"][0]
            lat, lon, city_name = result["latitude"], result["longitude"], result["name"]

        # 2. Weather API
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": "America/Sao_Paulo",
            "forecast_days": min(days, 16)
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        def _get_condition(code: int) -> str:
            return {0: "Limpo", 1: "Limpo", 2: "Parcialmente nublado", 3: "Nublado", 45: "Neblina", 51: "Garoa", 61: "Chuva leve", 95: "Tempestade"}.get(code, f"Cod {code}")

        current = data.get("current", {})
        daily = data.get("daily", {})
        
        result_data = {
            "location": city_name,
            "current": {"temp": current.get("temperature_2m"), "cond": _get_condition(current.get("weather_code"))},
            "forecast": [{"date": daily["time"][i], "cond": _get_condition(daily["weather_code"][i])} for i in range(min(len(daily.get("time", [])), days))]
        }
        return json.dumps(result_data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@ziva_tool
def get_air_quality(location: str = None) -> str:
    """
    Obtém qualidade do ar usando Open-Meteo Air Quality API.
    """
    if not location: return "Especifique a localização."
    try:
        # Geocoding reuse logic simplified here for brevity
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geocode_url, params={"name": location, "count": 1}, timeout=10)
        geo_data = geo_resp.json()
        if not geo_data.get("results"): return "Local não encontrado."
        result = geo_data["results"][0]
        
        air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        air_params = {"latitude": result["latitude"], "longitude": result["longitude"], "current": "us_aqi"}
        air_resp = requests.get(air_url, params=air_params, timeout=10)
        air_data = air_resp.json()
        
        aqi = air_data.get("current", {}).get("us_aqi", 0)
        return json.dumps({"location": result["name"], "aqi": aqi, "status": "Bom" if aqi <= 50 else "Moderado"}, ensure_ascii=False)
    except Exception as e:
        return str(e)
