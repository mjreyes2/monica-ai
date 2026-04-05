"""
World Information Utilities for Monica AI
Provides current time, timezone, and weather information.
"""

import datetime
import time
import requests
from typing import Dict, Optional, Any

# Try to get timezone info
try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False


def get_current_time() -> Dict[str, str]:
    """Get current local time information."""
    now = datetime.datetime.now()
    
    return {
        "time": now.strftime("%I:%M %p"),  # 12-hour format with AM/PM
        "time_24h": now.strftime("%H:%M"),
        "date": now.strftime("%B %d, %Y"),  # December 5, 2025
        "day": now.strftime("%A"),  # Thursday
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": int(time.time()),
        "timezone": time.tzname[0] if time.tzname else "Unknown"
    }


def get_timezone_info() -> Dict[str, Any]:
    """Get timezone information."""
    now = datetime.datetime.now()
    utc_offset = now.astimezone().strftime('%z')
    
    return {
        "timezone": time.tzname[0] if time.tzname else "Unknown",
        "utc_offset": utc_offset,
        "is_dst": time.daylight and time.localtime().tm_isdst > 0
    }


def get_weather(city: str = "auto") -> Optional[Dict[str, Any]]:
    """
    Get current weather information.
    Uses wttr.in free API (no API key required).
    
    Args:
        city: City name or "auto" for automatic location
        
    Returns:
        Weather information dict or None if failed
    """
    try:
        # wttr.in provides free weather data
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current = data.get("current_condition", [{}])[0]
            area = data.get("nearest_area", [{}])[0]
            
            return {
                "location": area.get("areaName", [{}])[0].get("value", city),
                "country": area.get("country", [{}])[0].get("value", ""),
                "temperature_c": current.get("temp_C", ""),
                "temperature_f": current.get("temp_F", ""),
                "feels_like_c": current.get("FeelsLikeC", ""),
                "feels_like_f": current.get("FeelsLikeF", ""),
                "condition": current.get("weatherDesc", [{}])[0].get("value", ""),
                "humidity": current.get("humidity", ""),
                "wind_mph": current.get("windspeedMiles", ""),
                "wind_kph": current.get("windspeedKmph", ""),
                "wind_direction": current.get("winddir16Point", ""),
                "uv_index": current.get("uvIndex", ""),
                "visibility_miles": current.get("visibilityMiles", ""),
                "pressure_mb": current.get("pressure", "")
            }
    except Exception as e:
        print(f"Weather fetch error: {e}")
    
    return None


def get_world_context() -> str:
    """
    Get a formatted string with current world context for Monica.
    Includes time, date, and weather.
    """
    time_info = get_current_time()
    
    context_parts = [
        f"Current time: {time_info['time']} ({time_info['day']}, {time_info['date']})",
        f"Timezone: {time_info['timezone']}"
    ]
    
    # Try to get weather (non-blocking, with short timeout)
    try:
        weather = get_weather("auto")
        if weather:
            context_parts.append(
                f"Weather in {weather['location']}: {weather['condition']}, "
                f"{weather['temperature_f']}°F ({weather['temperature_c']}°C), "
                f"Humidity: {weather['humidity']}%"
            )
    except Exception:
        pass
    
    return " | ".join(context_parts)


# Quick access functions
def what_time_is_it() -> str:
    """Simple function to get current time as spoken text."""
    info = get_current_time()
    return f"It's {info['time']} on {info['day']}, {info['date']}"


def what_is_the_weather() -> str:
    """Simple function to get weather as spoken text."""
    weather = get_weather("auto")
    if weather:
        return (f"In {weather['location']}, it's currently {weather['condition']} "
                f"with a temperature of {weather['temperature_f']} degrees Fahrenheit. "
                f"Humidity is {weather['humidity']} percent.")
    return "I couldn't fetch the weather information right now."
