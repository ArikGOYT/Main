"""
Модуль погоды - получение информации о погоде через API
"""
import requests
from config.settings import Settings


class WeatherModule:
    """Модуль получения погоды"""
    
    def __init__(self):
        self.api_key = Settings.GOOGLE_API_KEY  # Или OpenWeatherMap ключ
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    def get_weather(self, city="Москва"):
        """
        Получение погоды для города
        
        Args:
            city: название города
            
        Returns:
            str: информация о погоде
        """
        # Заглушка - требует настройки API ключа OpenWeatherMap
        return f"Погода в {city}: модуль требует настройки API ключа OpenWeatherMap 🌤️"
        
        # Пример реализации (раскомментировать при наличии ключа):
        # params = {
        #     'q': city,
        #     'appid': self.api_key,
        #     'units': 'metric',
        #     'lang': 'ru'
        # }
        # 
        # try:
        #     response = requests.get(self.base_url, params=params)
        #     data = response.json()
        #     
        #     if data['cod'] == 200:
        #         temp = data['main']['temp']
        #         feels_like = data['main']['feels_like']
        #         description = data['weather'][0]['description']
        #         humidity = data['main']['humidity']
        #         
        #         return (f"В {city} сейчас {description}, "
        #                f"температура {temp}°C (ощущается как {feels_like}°C), "
        #                f"влажность {humidity}%")
        #     else:
        #         return f"Не удалось получить погоду для {city}"
        #         
        # except Exception as e:
        #     return f"Ошибка при получении погоды: {e}"
