---
name: ath_weather
description: Get current weather for any city using the CLI Tools Hub weather command.
metadata: {"openclaw": {"requires": {"bins": ["ath"]}, "primaryEnv": "OPENWEATHERMAP_API_KEY"}}
input_schema:
  type: object
  properties:
    city:
      type: string
      description: City name (e.g. "London")
    units:
      type: string
      enum: [metric, imperial, standard]
      description: Temperature unit system (default metric)
  required: [city]
---

# Weather Lookup

When the user asks about current weather conditions for a city or location, use this tool.

## Usage

```bash
ath weather --city "<CITY_NAME>"
ath weather --city "<CITY_NAME>" --units imperial
```

## Output

Returns JSON with temperature, humidity, weather description, and wind speed.

```json
{
  "status": "ok",
  "data": {
    "city": "London",
    "country": "GB",
    "temperature": {"current": 15.2, "feels_like": 14.1, "unit": "°C"},
    "humidity": 72,
    "wind": {"speed": 3.6, "unit": "m/s"},
    "condition": {"summary": "Clouds", "description": "overcast clouds"}
  }
}
```

## Requirements

- Environment variable `OPENWEATHERMAP_API_KEY` must be set
- Install: `pip install cli-tools-hub`

## When to use

- User asks "what's the weather in Berlin?"
- User needs current temperature or conditions for a location
- User is planning something weather-dependent

## When NOT to use

- Historical weather data (use web search instead)
- Weather forecasts beyond current conditions
