"""Weather tool — Get current weather for any city via OpenWeatherMap."""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def _output(data, file=sys.stdout):
    print(json.dumps(data, indent=2), file=file)


def _error(message, code, exit_code):
    _output({"status": "error", "error": message, "code": code}, file=sys.stderr)
    sys.exit(exit_code)


def get_weather(city: str, units: str = "metric") -> dict:
    """Fetch current weather for a city from OpenWeatherMap.

    Args:
        city: City name (e.g., "London" or "London,GB").
        units: "metric", "imperial", or "standard".

    Returns:
        dict with structured weather data.
    """
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        _error("OPENWEATHERMAP_API_KEY environment variable is not set", "AUTH_MISSING", 2)

    params = urllib.parse.urlencode({"q": city, "appid": api_key, "units": units})
    url = f"{BASE_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            detail = json.loads(body).get("message", body)
        except json.JSONDecodeError:
            detail = body
        _error(f"API error {e.code}: {detail}", "API_ERROR", 1)
    except urllib.error.URLError as e:
        _error(f"Network error: {e.reason}", "API_ERROR", 1)

    unit_labels = {"metric": "°C", "imperial": "°F", "standard": "K"}
    speed_labels = {"metric": "m/s", "imperial": "mph", "standard": "m/s"}

    return {
        "city": data.get("name"),
        "country": data.get("sys", {}).get("country"),
        "coordinates": {
            "lat": data.get("coord", {}).get("lat"),
            "lon": data.get("coord", {}).get("lon"),
        },
        "temperature": {
            "current": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "min": data.get("main", {}).get("temp_min"),
            "max": data.get("main", {}).get("temp_max"),
            "unit": unit_labels[units],
        },
        "humidity": data.get("main", {}).get("humidity"),
        "pressure_hpa": data.get("main", {}).get("pressure"),
        "wind": {
            "speed": data.get("wind", {}).get("speed"),
            "unit": speed_labels[units],
            "direction_degrees": data.get("wind", {}).get("deg"),
        },
        "condition": {
            "summary": data.get("weather", [{}])[0].get("main"),
            "description": data.get("weather", [{}])[0].get("description"),
            "icon": data.get("weather", [{}])[0].get("icon"),
        },
        "visibility_meters": data.get("visibility"),
        "clouds_percent": data.get("clouds", {}).get("all"),
    }


def run(args):
    """CLI entrypoint for weather tool."""
    result = get_weather(args.city, args.units)
    _output({"status": "ok", "data": result})
