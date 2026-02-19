"""
Weather service - same API as RA_Backend
"""
import os
import httpx
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

class WeatherService:
    """Fetch weather data using same API as RA_Backend"""
    
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API")  # Same as RA_Backend
        
    async def get_location_from_ip(self) -> Tuple[float, float, str]:
        """Get location from IP - try multiple services"""
        # Try ipapi.co first (same as RA_Backend)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://ipapi.co/json/", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    lat = data.get('latitude')
                    lon = data.get('longitude')
                    city = data.get('city')
                    country = data.get('country_name')
                    
                    if lat and lon and city:
                        location_name = f"{city}, {country}" if country else city
                        print(f"✅ Detected location: {location_name} ({lat}, {lon})")
                        return lat, lon, location_name
        except Exception as e:
            print(f"⚠️ ipapi.co failed: {e}")
        
        # Try ip-api.com as backup
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://ip-api.com/json/", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        lat = data.get('lat')
                        lon = data.get('lon')
                        city = data.get('city')
                        country = data.get('country')
                        
                        if lat and lon and city:
                            location_name = f"{city}, {country}" if country else city
                            print(f"✅ Detected location (backup): {location_name} ({lat}, {lon})")
                            return lat, lon, location_name
        except Exception as e:
            print(f"⚠️ ip-api.com failed: {e}")
        
        # Fallback to Mekong Delta
        print("⚠️ Using fallback location: Mekong Delta, Vietnam")
        return 10.0, 106.0, "Mekong Delta, Vietnam"
    
    async def fetch_weather_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeather API - same as RA_Backend"""
        if not self.api_key:
            print("⚠️ WEATHER_API not set, using fallback")
            return self._get_fallback_weather(lat, lon)
        
        try:
            async with httpx.AsyncClient() as client:
                # Current weather
                current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
                current_response = await client.get(current_url, timeout=10)
                
                if current_response.status_code != 200:
                    print(f"⚠️ Weather API returned {current_response.status_code}")
                    return self._get_fallback_weather(lat, lon)
                
                current_data = current_response.json()
                
                # 5-day forecast
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
                forecast_response = await client.get(forecast_url, timeout=10)
                forecast_data = forecast_response.json() if forecast_response.status_code == 200 else None
                
                return self._parse_weather_data(current_data, forecast_data, lat, lon)
                
        except Exception as e:
            print(f"⚠️ Weather API error: {e}")
            return self._get_fallback_weather(lat, lon)
    
    def _parse_weather_data(self, current: Dict, forecast: Optional[Dict], lat: float, lon: float) -> Dict[str, Any]:
        """Parse OpenWeather response"""
        # Calculate 7-day rain forecast
        rain_7d = 0
        if forecast and "list" in forecast:
            for item in forecast["list"][:56]:  # 7 days * 8 (3-hour intervals)
                if "rain" in item and "3h" in item["rain"]:
                    rain_7d += item["rain"]["3h"]
        
        # Convert wind speed from m/s to km/h
        wind_ms = current.get("wind", {}).get("speed", 0)
        wind_kmh = round(wind_ms * 3.6)
        
        # Get visibility in km
        visibility_m = current.get("visibility", 10000)
        visibility_km = round(visibility_m / 1000, 1)
        
        result = {
            "temperature_c": round(current["main"]["temp"]),
            "humidity_pct": current["main"]["humidity"],
            "wind_speed_kmh": wind_kmh,
            "visibility_km": visibility_km,
            "location": current.get("name", "Unknown"),
            "country": current.get("sys", {}).get("country", ""),
            "description": current["weather"][0]["description"],
            "rain_forecast_7d_mm": round(rain_7d, 1),
            "lat": lat,
            "lon": lon,
            "source": "openweather_api"
        }
        
        return result
    
    def _get_fallback_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fallback weather based on coordinates"""
        # Tropical rice-growing regions default
        return {
            "temperature_c": 28,
            "humidity_pct": 75,
            "location": f"Location ({lat:.2f}, {lon:.2f})",
            "description": "tropical climate",
            "rain_forecast_7d_mm": 15,
            "lat": lat,
            "lon": lon,
            "source": "estimated"
        }
    
    async def auto_fetch_and_update(self, farm_state) -> Dict[str, Any]:
        """Auto-fetch weather based on IP and update farm state"""
        # Get location from IP
        lat, lon, location_name = await self.get_location_from_ip()
        
        # Fetch weather for that location
        weather = await self.fetch_weather_data(lat, lon)
        
        if weather:
            updates = {
                "farm.location": location_name,
                "weather.forecast_rain_next_7d_mm": weather["rain_forecast_7d_mm"],
                "weather.temp_avg": weather.get("temperature_c")
            }
            # Update farm state with provenance (if available)
            if hasattr(farm_state, "update_from_dict"):
                farm_state.update_from_dict(updates, source="weather_service", confidence=0.9)
            else:
                farm_state.farm.location = location_name
                farm_state.weather.forecast_rain_next_7d_mm = weather["rain_forecast_7d_mm"]
                farm_state.weather.temp_avg = weather.get("temperature_c")
            
            return {
                "success": True,
                "location": location_name,
                "temperature": weather["temperature_c"],
                "humidity": weather.get("humidity_pct"),
                "wind_speed": weather.get("wind_speed_kmh"),
                "visibility": weather.get("visibility_km"),
                "rain_forecast": weather["rain_forecast_7d_mm"],
                "description": weather.get("description"),
                "source": weather.get("source", "api")
            }
        
        return {"success": False}
