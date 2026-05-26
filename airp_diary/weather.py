"""
天气API集成 - 支持多个天气数据源

新增 2026.05 update:
- open_meteo: 完全免费、免注册、免key（推荐）
- wttr:       完全免费、免注册、免key（最简单的备选）
- openweather/heweather/caiyun: 需要 API Key
"""

import aiohttp
import urllib.parse
from typing import Optional
from enum import Enum

EMOJI_MAP = {
    "晴": "☀️",
    "多云": "⛅",
    "阴": "☁️",
    "小雨": "🌦️",
    "雨": "🌧️",
    "大雨": "⛈️",
    "雪": "❄️",
    "大风": "💨",
    "阵雨": "🌧️",
    "雾": "🌫️",
    "毛毛雨": "🌦️",
    "雷": "⛈️",
    "冰雹": "🌨️",
}

# WMO Weather code 映射 (Open-Meteo 使用)
WMO_CODE_MAP = {
    0: "晴",
    1: "大致晴朗", 2: "局部多云", 3: "阴",
    45: "雾", 48: "霾雾",
    51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨",
    56: "冻毛毛雨", 57: "冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "冻雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    77: "雪粒",
    80: "阵雨", 81: "强阵雨", 82: "暴阵雨",
    85: "阵雪", 86: "强阵雪",
    95: "雷阵雨",
    96: "雷暴冰雹", 99: "强雷暴冰雹",
}


class WeatherProvider(Enum):
    """天气提供商"""

    OPEN_METEO = "open_meteo"      # 免费免注册 ✨
    WTTR = "wttr"                  # 免费免注册 ✨
    OPENWEATHER = "openweather"    # 需要 API Key
    HEWEATHER = "heweather"        # 需要 API Key
    CAIYUN = "caiyun"              # 需要 API Key


class WeatherAPI:
    """天气API管理器"""

    def __init__(self, provider: str = "open_meteo", api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key

    async def get_weather(self, city: str) -> Optional[str]:
        """
        获取天气信息

        Args:
            city: 城市名称（中英文都行）

        Returns:
            str: 格式为 "🌤️ 晴朗 / 22℃" 的天气字符串
        """
        if self.provider == "open_meteo":
            return await self._open_meteo(city)
        elif self.provider == "wttr":
            return await self._wttr(city)
        elif self.provider == "openweather":
            return await self._openweather(city)
        elif self.provider == "heweather":
            return await self._heweather(city)
        elif self.provider == "caiyun":
            return await self._caiyun(city)
        else:
            return self._default_weather()

    # ============ 免费免注册 providers ============

    async def _open_meteo(self, city: str) -> Optional[str]:
        """
        Open-Meteo: 完全免费、免key、免注册
        步骤：1) Geocoding 把城市名转坐标 2) 取当前天气
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: geocoding
                geo_url = "https://geocoding-api.open-meteo.com/v1/search"
                geo_params = {"name": city, "count": 1, "language": "zh"}
                async with session.get(
                    geo_url,
                    params=geo_params,
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as resp:
                    if resp.status != 200:
                        return None
                    geo_data = await resp.json()
                    results = geo_data.get("results", [])
                    if not results:
                        return None
                    lat = results[0]["latitude"]
                    lon = results[0]["longitude"]

                # Step 2: forecast
                fc_url = "https://api.open-meteo.com/v1/forecast"
                fc_params = {
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,weather_code",
                    "timezone": "auto",
                }
                async with session.get(
                    fc_url,
                    params=fc_params,
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    current = data.get("current", {})
                    code = current.get("weather_code", 0)
                    temp = current.get("temperature_2m", 20)

                    desc = WMO_CODE_MAP.get(int(code), "晴")
                    emoji = self._get_emoji(desc)
                    return f"{emoji} {desc} / {int(round(temp))}℃"
        except Exception as e:
            print(f"[airp_diary] Open-Meteo error: {e}")
        return None

    async def _wttr(self, city: str) -> Optional[str]:
        """
        wttr.in: 完全免费、免key、免注册，直接URL访问
        """
        try:
            # wttr.in 支持 ?format=j1 返回JSON，中文城市需要URL编码
            encoded = urllib.parse.quote(city)
            url = f"https://wttr.in/{encoded}?format=j1&lang=zh"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    current = (data.get("current_condition") or [{}])[0]

                    # wttr 的中文描述在 lang_zh 字段
                    desc_zh = current.get("lang_zh", [{}])
                    if isinstance(desc_zh, list) and desc_zh:
                        desc = desc_zh[0].get("value", "晴")
                    else:
                        desc = current.get("weatherDesc", [{}])[0].get("value", "晴")

                    temp = current.get("temp_C", "20")
                    emoji = self._get_emoji(desc)
                    return f"{emoji} {desc} / {temp}℃"
        except Exception as e:
            print(f"[airp_diary] wttr.in error: {e}")
        return None

    # ============ 需要 API Key 的 providers ============

    async def _openweather(self, city: str) -> Optional[str]:
        """OpenWeather - 需 API Key"""
        if not self.api_key:
            return None
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "zh_cn",
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        weather_desc = data["weather"][0]["description"]
                        temp = int(data["main"]["temp"])
                        emoji = self._get_emoji(weather_desc)
                        return f"{emoji} {weather_desc} / {temp}℃"
        except Exception as e:
            print(f"[airp_diary] OpenWeather error: {e}")
        return None

    async def _heweather(self, city: str) -> Optional[str]:
        """和风天气 - 需 API Key（注：新版API改用JWT，本实现走旧版 key 参数）"""
        if not self.api_key:
            return None
        try:
            url = "https://api.qweather.com/v7/weather/now"
            params = {"location": city, "key": self.api_key}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        weather_desc = data["now"]["text"]
                        temp = int(data["now"]["temp"])
                        emoji = self._get_emoji(weather_desc)
                        return f"{emoji} {weather_desc} / {temp}℃"
        except Exception as e:
            print(f"[airp_diary] HeWeather error: {e}")
        return None

    async def _caiyun(self, city: str) -> Optional[str]:
        """彩云天气 - 需 API Key（暂未实现完整坐标查询）"""
        if not self.api_key:
            return None
        print("[airp_diary] 彩云天气暂未实现完整查询")
        return None

    @staticmethod
    def _get_emoji(weather_text: str) -> str:
        """根据天气描述获取emoji"""
        for key, emoji in EMOJI_MAP.items():
            if key in weather_text:
                return emoji
        return "🌤️"

    @staticmethod
    def _default_weather() -> str:
        """返回默认天气（按季节）"""
        import random
        from datetime import datetime

        month = datetime.now().month
        if month in [12, 1, 2]:
            weathers = ["☃️ 冬日晴朗 / 5℃", "☁️ 阴沉 / 3℃", "🌨️ 飘雪 / 0℃"]
        elif month in [3, 4, 5]:
            weathers = ["☀️ 春日晴朗 / 18℃", "🌦️ 多云 / 16℃", "🌧️ 春雨 / 14℃"]
        elif month in [6, 7, 8]:
            weathers = ["☀️ 炎热晴朗 / 28℃", "⛅ 多云 / 26℃", "🌧️ 午后雷阵雨 / 24℃"]
        else:
            weathers = ["☀️ 秋日晴朗 / 22℃", "⛅ 凉爽 / 20℃", "🌧️ 秋雨 / 18℃"]
        return random.choice(weathers)


# 全局天气API实例
_weather_api: Optional[WeatherAPI] = None


def init_weather_api(
    provider: str = "open_meteo", api_key: Optional[str] = None
) -> WeatherAPI:
    """初始化全局天气API"""
    global _weather_api
    _weather_api = WeatherAPI(provider, api_key)
    return _weather_api


def get_weather_api() -> WeatherAPI:
    """获取全局天气API实例"""
    global _weather_api
    if _weather_api is None:
        _weather_api = WeatherAPI()
    return _weather_api