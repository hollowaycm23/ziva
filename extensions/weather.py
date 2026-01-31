import logging
import requests
from typing import Optional, Dict, Any
from agent.tools import ziva_tool

logger = logging.getLogger("WeatherTools")


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
        return "Para fornecer a previsão do tempo, preciso que você informe de qual cidade ou local deseja saber. Por favor, especifique a cidade."

    import requests
    import logging
    import json
    from datetime import datetime, timedelta

    logger = logging.getLogger("WeatherTools")

    try:
        # 1. Geocoding
        # Allow lat,lon input or city name
        if ',' in location and location.replace(
                ',', '').replace('.', '').replace('-', '').isdigit():
            lat, lon = map(float, location.split(','))
            city_name = f"Lat {lat}, Lon {lon}"
        else:
            geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_params = {
                "name": location,
                "count": 1,
                "language": "pt",
                "format": "json"}
            geo_resp = requests.get(geocode_url, params=geo_params, timeout=10)

            if geo_resp.status_code != 200:
                return json.dumps(
                    {"error": f"Erro Geocoding: {geo_resp.text}"})

            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                return json.dumps(
                    {"error": f"Localização '{location}' não encontrada."})

            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            city_name = result["name"]

        # 2. Weather API Call (JSON)
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": "America/Sao_Paulo",
            "forecast_days": min(
                days,
                16)}

        # Plain request with timeout
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return json.dumps({"error": f"Erro Weather API: {response.text}"})

        data = response.json()

        # Helper for WMO codes
        def _get_weather_condition(code: int) -> str:
            conditions = {
                0: "Céu limpo",
                1: "Principalmente limpo",
                2: "Parcialmente nublado",
                3: "Nublado",
                45: "Neblina",
                48: "Neblina com geada",
                51: "Garoa leve",
                53: "Garoa moderada",
                55: "Garoa forte",
                61: "Chuva leve",
                63: "Chuva moderada",
                65: "Chuva forte",
                71: "Neve leve",
                73: "Neve moderada",
                75: "Neve forte",
                77: "Granizo",
                80: "Pancadas de chuva leves",
                81: "Pancadas de chuva moderadas",
                82: "Pancadas de chuva fortes",
                85: "Pancadas de neve leves",
                86: "Pancadas de neve fortes",
                95: "Tempestade",
                96: "Tempestade com granizo leve",
                99: "Tempestade com granizo forte"}
            return conditions.get(code, f"Código {code}")

        # Parse Current Data
        current = data.get("current", {})
        current_data = {
            "temperature": current.get("temperature_2m"),
            "condition": _get_weather_condition(current.get("weather_code")),
            "wind_speed": current.get("wind_speed_10m")
        }

        # Parse Daily Data
        daily = data.get("daily", {})
        forecast_list = []

        times = daily.get("time", [])
        codes = daily.get("weather_code", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precips = daily.get("precipitation_sum", [])
        max_winds = daily.get("wind_speed_10m_max", [])

        count = min(len(times), days)

        for i in range(count):
            forecast_list.append({
                "date": times[i],
                "min_temp": min_temps[i],
                "max_temp": max_temps[i],
                "condition": _get_weather_condition(codes[i]),
                "precipitation": precips[i],
                "max_wind": max_winds[i]
            })

        result_data = {
            "location": city_name,
            "current": current_data,
            "forecast": forecast_list,
            "source": "Open-Meteo"
        }

        return json.dumps(result_data, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Erro ao processar clima (JSON): {e}")
        return json.dumps({"error": str(e)})


@ziva_tool
def get_air_quality(location: str = None) -> str:
    """
    Obtém qualidade do ar usando Open-Meteo Air Quality API.

    Args:
        location: Nome da cidade ou coordenadas

    Returns:
        str: Dados de qualidade do ar
    """
    if not location:
        return "Para verificar a qualidade do ar, preciso saber a cidade ou local. Por favor, especifique."
    import requests
    import logging
    logger = logging.getLogger("WeatherTools")

    def _get_aqi_level(aqi: int) -> str:
        """Converte AQI para nível de qualidade."""
        if aqi <= 50:
            return "🟢 Bom"
        elif aqi <= 100:
            return "🟡 Moderado"
        elif aqi <= 150:
            return "🟠 Insalubre para grupos sensíveis"
        elif aqi <= 200:
            return "🔴 Insalubre"
        elif aqi <= 300:
            return "🟣 Muito insalubre"
        else:
            return "🟤 Perigoso"

    import json

    try:
        # Geocoding
        if ',' in location and location.replace(
                ',', '').replace('.', '').replace('-', '').isdigit():
            lat, lon = map(float, location.split(','))
            city_name = f"Lat {lat}, Lon {lon}"
        else:
            geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_params = {
                "name": location,
                "count": 1,
                "language": "pt",
                "format": "json"}

            geo_resp = requests.get(geocode_url, params=geo_params, timeout=10)
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                return json.dumps(
                    {"error": f"Localização '{location}' não encontrada."})

            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            city_name = result["name"]

        # Obter qualidade do ar
        air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        air_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,us_aqi",
            "timezone": "America/Sao_Paulo"}

        air_resp = requests.get(air_url, params=air_params, timeout=10)
        air_data = air_resp.json()

        result_data = {
            "location": city_name,
            "aqi": 0,
            "aqi_status": "Unknown",
            "pollutants": {}
        }

        if "current" in air_data:
            current = air_data["current"]
            aqi = current.get("us_aqi", 0)
            result_data["aqi"] = aqi
            result_data["aqi_status"] = _get_aqi_level(aqi)
            result_data["pollutants"] = {
                "pm2_5": current.get('pm2_5'),
                "pm10": current.get('pm10'),
                "co": current.get('carbon_monoxide'),
                "no2": current.get('nitrogen_dioxide'),
                "o3": current.get('ozone')
            }

        return json.dumps(result_data, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Erro ao obter qualidade do ar: {e}")
        return json.dumps({"error": str(e)})
