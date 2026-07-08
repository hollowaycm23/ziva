import requests
from typing import Dict, Any


class WeatherClient:
    """
    Client for interacting with Open-Meteo Weather API.
    """

    def get_weather(self, location: str, days: int = 3) -> Dict[str, Any]:
        """
        Gets weather forecast for a location.
        """
        try:
            lat, lon, city_name = self._geocode(location)
            if not lat:
                return {"error": f"Location '{location}' not found."}
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_sum"
                ),
                "timezone": "America/Sao_Paulo",
                "forecast_days": min(days, 7)}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return {"error": f"Weather API Error: {response.text}"}
            data = response.json()
            current = data.get("current", {})
            daily = data.get("daily", {})
            forecast_str = f"Clima atual em {city_name}:\n"
            forecast_str += f"- Temp: {current.get('temperature_2m')}°C\n"
            forecast_str += (f"- Condição: "
                             f"{self._get_condition(current.get('weather_code'))}\n\n")
            forecast_str += "Previsão:\n"
            for i in range(len(daily.get("time", []))):
                date = daily["time"][i]
                max_t = daily["temperature_2m_max"][i]
                min_t = daily["temperature_2m_min"][i]
                code = daily["weather_code"][i]
                forecast_str += (f"- {date}: Min {min_t}°C / Max {max_t}°C "
                                 f"({self._get_condition(code)})\n")
            return {"result": forecast_str}
        except Exception as e:
            return {"error": str(e)}

    def _geocode(self, location: str):
        try:
            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                "name": location,
                "count": 1,
                "language": "pt",
                "format": "json"}
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            if data.get("results"):
                res = data["results"][0]
                return res["latitude"], res["longitude"], res["name"]
        except Exception:
            pass
        return None, None, None

    def _get_condition(self, code: int) -> str:
        conditions = {
            0: "Céu limpo", 1: "Limpo", 2: "Parcialmente nublado",
            3: "Nublado", 45: "Neblina", 51: "Garoa",
            61: "Chuva leve", 63: "Chuva", 80: "Pancadas de chuva",
            95: "Tempestade"}
        return conditions.get(code, "Desconhecido")