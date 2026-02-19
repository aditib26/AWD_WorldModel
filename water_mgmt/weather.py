"""Weather data adapter interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .schemas import WeatherSummary


class WeatherAdapter(ABC):
    """Interface for weather data providers"""
    
    @abstractmethod
    def get_forecast(self, location: Dict[str, Any]) -> WeatherSummary:
        """Get weather forecast for location"""
        pass
    
    @abstractmethod
    def get_multi_day_forecast(self, location: Dict[str, Any], days: int = 7) -> List[WeatherSummary]:
        """Get multi-day forecast"""
        pass


class StubWeatherAdapter(WeatherAdapter):
    """Manual input weather adapter for development"""
    
    def __init__(
        self,
        default_rain_24h: float = 0.0,
        default_rain_72h: float = 5.0,
        default_et0: float = 5.0,
        default_temp: float = 30.0
    ):
        self.default_rain_24h = default_rain_24h
        self.default_rain_72h = default_rain_72h
        self.default_et0 = default_et0
        self.default_temp = default_temp
        
        # Manual overrides
        self.overrides = {}
    
    def set_weather(
        self,
        rain_24h: float = None,
        rain_72h: float = None,
        et0: float = None,
        temp: float = None
    ):
        """Manually set weather values"""
        if rain_24h is not None:
            self.overrides["rain_24h"] = rain_24h
        if rain_72h is not None:
            self.overrides["rain_72h"] = rain_72h
        if et0 is not None:
            self.overrides["et0"] = et0
        if temp is not None:
            self.overrides["temp"] = temp
    
    def get_forecast(self, location: Dict[str, Any]) -> WeatherSummary:
        """Return configured weather values"""
        return WeatherSummary(
            rain_last_24h_mm=self.overrides.get("rain_24h", self.default_rain_24h),
            rain_next_72h_mm=self.overrides.get("rain_72h", self.default_rain_72h),
            et0_next_24h_mm=self.overrides.get("et0", self.default_et0),
            temperature_next_24h_c=self.overrides.get("temp", self.default_temp),
            forecast_confidence="medium"
        )
    
    def get_multi_day_forecast(self, location: Dict[str, Any], days: int = 7) -> List[WeatherSummary]:
        """Return same forecast for all days"""
        base = self.get_forecast(location)
        return [base for _ in range(days)]


class OpenWeatherAdapter(WeatherAdapter):
    """OpenWeatherMap API integration — current weather + 5-day forecast"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # Mekong Delta province coordinates (lat, lon)
    PROVINCE_COORDS = {
        "an giang":       (10.39, 105.44),
        "dong thap":      (10.45, 105.63),
        "long an":        (10.54, 106.41),
        "tien giang":     (10.35, 106.36),
        "ben tre":        (10.24, 106.38),
        "vinh long":      (10.25, 105.97),
        "tra vinh":       (9.93,  106.34),
        "hau giang":      (9.78,  105.47),
        "soc trang":      (9.60,  105.97),
        "bac lieu":       (9.29,  105.72),
        "ca mau":         (9.18,  105.15),
        "kien giang":     (10.01, 105.08),
        "can tho":        (10.03, 105.77),
    }
    DEFAULT_COORDS = (10.03, 105.77)  # Can Tho (central Mekong Delta)
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._cache: Dict[str, Any] = {}
        self._cache_ts: float = 0
        self._cache_ttl: float = 1800  # 30 min cache
    
    def _get_coords(self, location: Dict[str, Any]) -> tuple:
        province = (location.get("province") or "").strip().lower()
        return self.PROVINCE_COORDS.get(province, self.DEFAULT_COORDS)
    
    def _fetch_current(self, lat: float, lon: float) -> Dict:
        import requests, time
        cache_key = f"current_{lat}_{lon}"
        now = time.time()
        if cache_key in self._cache and (now - self._cache_ts) < self._cache_ttl:
            return self._cache[cache_key]
        
        resp = requests.get(
            f"{self.BASE_URL}/weather",
            params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        self._cache[cache_key] = data
        self._cache_ts = now
        return data
    
    def _fetch_forecast(self, lat: float, lon: float) -> Dict:
        import requests, time
        cache_key = f"forecast_{lat}_{lon}"
        now = time.time()
        if cache_key in self._cache and (now - self._cache_ts) < self._cache_ttl:
            return self._cache[cache_key]
        
        resp = requests.get(
            f"{self.BASE_URL}/forecast",
            params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        self._cache[cache_key] = data
        self._cache_ts = now
        return data
    
    def _estimate_et0(self, temp_c: float) -> float:
        """Simplified Hargreaves ET0 estimate from temperature (mm/day)"""
        # Rough approximation for tropical lowland: ET0 ≈ 0.0023 * (T+17.8) * sqrt(Trange) * Ra
        # Simplified for Mekong Delta: ~4-6 mm/day typical
        if temp_c > 35:
            return 6.0
        elif temp_c > 30:
            return 5.0
        elif temp_c > 25:
            return 4.0
        else:
            return 3.0
    
    def get_forecast(self, location: Dict[str, Any]) -> WeatherSummary:
        """Fetch current + forecast from OpenWeatherMap"""
        lat, lon = self._get_coords(location)
        
        try:
            current = self._fetch_current(lat, lon)
            forecast = self._fetch_forecast(lat, lon)
            
            # Rain last 24h from current weather (OWM gives rain.1h or rain.3h)
            rain_data = current.get("rain", {})
            rain_1h = rain_data.get("1h", 0.0)
            rain_last_24h = rain_1h * 24  # rough estimate from current rate
            
            # Better: sum past entries if available, else use current rate
            # OWM free tier doesn't give historical, so this is an approximation
            
            # Rain next 72h from forecast (3-hour intervals, sum first 24 entries = 72h)
            rain_next_72h = 0.0
            rain_next_24h_entries = []
            for entry in forecast.get("list", [])[:24]:  # 24 × 3h = 72h
                entry_rain = entry.get("rain", {}).get("3h", 0.0)
                rain_next_72h += entry_rain
                if len(rain_next_24h_entries) < 8:  # first 24h
                    rain_next_24h_entries.append(entry)
            
            # Temperature from first forecast entry
            temp = current.get("main", {}).get("temp", 30.0)
            
            # ET0 estimate
            et0 = self._estimate_et0(temp)
            
            return WeatherSummary(
                rain_last_24h_mm=round(rain_last_24h, 1),
                rain_next_72h_mm=round(rain_next_72h, 1),
                et0_next_24h_mm=et0,
                temperature_next_24h_c=round(temp, 1),
                forecast_confidence="high" if len(forecast.get("list", [])) >= 24 else "medium"
            )
        
        except Exception as e:
            # Fallback to conservative defaults on API failure
            print(f"⚠️ Weather API error: {e}, using defaults")
            return WeatherSummary(
                rain_last_24h_mm=0.0,
                rain_next_72h_mm=5.0,
                et0_next_24h_mm=5.0,
                temperature_next_24h_c=30.0,
                forecast_confidence="low"
            )
    
    def get_multi_day_forecast(self, location: Dict[str, Any], days: int = 7) -> List[WeatherSummary]:
        """Parse 5-day forecast into daily summaries"""
        lat, lon = self._get_coords(location)
        
        try:
            forecast = self._fetch_forecast(lat, lon)
            entries = forecast.get("list", [])
            
            # Group by day (8 entries per day at 3h intervals)
            daily_summaries = []
            for day_idx in range(min(days, 5)):  # OWM free gives 5 days max
                start = day_idx * 8
                end = start + 8
                day_entries = entries[start:end]
                
                if not day_entries:
                    break
                
                # Sum rain for this day
                day_rain = sum(e.get("rain", {}).get("3h", 0.0) for e in day_entries)
                
                # Avg temperature
                temps = [e.get("main", {}).get("temp", 30.0) for e in day_entries]
                avg_temp = sum(temps) / len(temps) if temps else 30.0
                
                # Rain next 72h = sum of next 3 days from this day
                rain_72h = 0.0
                for future_day in range(3):
                    fi = (day_idx + future_day) * 8
                    fe = fi + 8
                    rain_72h += sum(e.get("rain", {}).get("3h", 0.0) for e in entries[fi:fe])
                
                daily_summaries.append(WeatherSummary(
                    rain_last_24h_mm=round(day_rain, 1),
                    rain_next_72h_mm=round(rain_72h, 1),
                    et0_next_24h_mm=self._estimate_et0(avg_temp),
                    temperature_next_24h_c=round(avg_temp, 1),
                    forecast_confidence="high" if len(day_entries) >= 6 else "medium"
                ))
            
            # Pad remaining days with last known or defaults
            while len(daily_summaries) < days:
                daily_summaries.append(daily_summaries[-1] if daily_summaries else WeatherSummary(
                    rain_last_24h_mm=0.0, rain_next_72h_mm=5.0,
                    et0_next_24h_mm=5.0, temperature_next_24h_c=30.0,
                    forecast_confidence="low"
                ))
            
            return daily_summaries[:days]
        
        except Exception as e:
            print(f"⚠️ Weather forecast API error: {e}, using defaults")
            default = WeatherSummary(
                rain_last_24h_mm=0.0, rain_next_72h_mm=5.0,
                et0_next_24h_mm=5.0, temperature_next_24h_c=30.0,
                forecast_confidence="low"
            )
            return [default for _ in range(days)]
