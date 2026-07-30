"""
Конфигурация ассистента
"""
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Settings:
    # API ключи
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    
    # Голосовые настройки
    VOICE_LANGUAGE = os.getenv('VOICE_LANGUAGE', 'ru-RU')
    VOICE_SPEED = float(os.getenv('VOICE_SPEED', '1.0'))
    
    # Имя ассистента
    ASSISTANT_NAME = os.getenv('ASSISTANT_NAME', 'Джарвис')
    
    # Слово активации
    WAKE_WORD = os.getenv('WAKE_WORD', 'джарвис').lower()
    
    # Режим отладки
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Папки проекта
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    
    @classmethod
    def is_configured(cls):
        """Проверка, настроены ли API ключи"""
        return bool(cls.OPENAI_API_KEY or cls.GOOGLE_API_KEY)
