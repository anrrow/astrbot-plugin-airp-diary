"""
天气API集成 - 支持多个天气数据源
"""

import aiohttp
from typing import Optional, Tuple
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
}


class WeatherProvider(Enum):
    """天气提供商"""

    OPENWEATHER = "openweather"
    HEWEATHER = "heweather"  # 和风天气
    CAIYUN = "caiyun"  # 彩云天气


class WeatherAPI:
    """天气API管理器"""

    def __init__(self, provider: str = "openweather", api_key: Optional[str] = None):
        """
        初始化天气API
        
        Args:
            provider: 天气源（openweather/heweather/caiyun）
            api_key: API密钥
        """
        self.provider = provider
        self.api_key = api_key

    async def get_weather(self, city: str) -> Optional[str]:
        """
        获取天气信息
        
        Args:
            city: 城市名称
            
        Returns:
            str: 格式为 "🌤️ 晴朗 / 22℃" 的天气字符串
        """
        if self.provider == "openweather":
            return await self._openweather(city)
        elif self.provider == "heweather":
            return await self._heweather(city)
        elif self.provider == "caiyun":
            return await self._caiyun(city)
        else:
            return self._default_weather()

    async def _openweather(self, city: str) -> Optional[str]:
        """获取OpenWeather数据"""
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
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        weather_desc = data["weather"][0]["description"]
                        temp = int(data["main"]["temp"])

                        emoji = self._get_emoji(weather_desc)
                        return f"{emoji} {weather_desc} / {temp}℃"
        except Exception as e:
            print(f"OpenWeather API error: {e}")

        return None

    async def _heweather(self, city: str) -> Optional[str]:
        """获取和风天气数据"""
        if not self.api_key:
            return None

        try:
            url = "https://api.qweather.com/v7/weather/now"
            params = {
                "location": city,
                "key": self.api_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        weather_desc = data["now"]["text"]
                        temp = int(data["now"]["temp"])

                        emoji = self._get_emoji(weather_desc)
                        return f"{emoji} {weather_desc} / {temp}℃"
        except Exception as e:
            print(f"HeWeather API error: {e}")

        return None

    async def _caiyun(self, city: str) -> Optional[str]:
        """获取彩云天气数据"""
        if not self.api_key:
            return None

        try:
            # 彩云天气需要先获取坐标
            # 这是简化版本，实际使用需要先获取城市坐标
            url = "https://api.caiyunapp.com/v2.5/weather"
            # 需要城市的经纬度
            # 这里省略具体实现
            pass
        except Exception as e:
            print(f"Caiyun API error: {e}")

        return None

    @staticmethod
    def _get_emoji(weather_text: str) -> str:
        """根据天气描述获取emoji"""
        for key, emoji in EMOJI_MAP.items():
            if key in weather_text:
                return emoji
        return "🌤️"  # 默认emoji

    @staticmethod
    def _default_weather() -> str:
        """返回默认天气"""
        import random
        from datetime import datetime

        # 根据月份推断季节
        month = datetime.now().month
        if month in [12, 1, 2]:
            weathers = ["☃️ 冬日晴朗 / 5℃", "☁️ 阴沉 / 3℃", "🌨️ 飘雪 / 0℃"]
        elif month in [3, 4, 5]:
            weathers = ["☀️ 春日晴朗 / 18℃", "🌦️ 多云 / 16℃", "🌧️ 春雨 / 14℃"]
        elif month in [6, 7, 8]:
            weathers = ["☀️ 炎热晴朗 / 28℃", "⛅ 多云 / 26℃", "🌧️ 午后雷阵雨 / 24℃"]
        else:  # 9, 10, 11
            weathers = ["☀️ 秋日晴朗 / 22℃", "⛅ 凉爽 / 20℃", "🌧️ 秋雨 / 18℃"]

        return random.choice(weathers)


# 全局天气API实例
_weather_api: Optional[WeatherAPI] = None


def init_weather_api(provider: str = "openweather", api_key: Optional[str] = None) -> WeatherAPI:
    """
    初始化全局天气API
    
    Args:
        provider: 天气源
        api_key: API密钥
        
    Returns:
        WeatherAPI: 天气API实例
    """
    global _weather_api
    _weather_api = WeatherAPI(provider, api_key)
    return _weather_api


def get_weather_api() -> WeatherAPI:
    """获取全局天气API实例"""
    global _weather_api
    if _weather_api is None:
        _weather_api = WeatherAPI()  # 使用默认天气
    return _weather_api
