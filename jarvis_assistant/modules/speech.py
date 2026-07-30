"""
Модуль работы с голосом: распознавание речи и синтез (TTS)
"""
import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
from playsound import playsound
import pyttsx3

from config.settings import Settings


class VoiceManager:
    """Управление голосовым вводом и выводом"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.language = Settings.VOICE_LANGUAGE
        
        # Инициализация офлайн TTS
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Скорость речи
        
        # Настройка микрофона
        with self.microphone as source:
            print("🎤 Настройка микрофона...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Микрофон готов")
    
    def listen(self, timeout=5, phrase_time_limit=10):
        """
        Распознавание речи с микрофона
        
        Args:
            timeout: время ожидания начала речи
            phrase_time_limit: максимальная длительность фразы
            
        Returns:
            str: распознанный текст или None
        """
        try:
            with self.microphone as source:
                print("👂 Слушаю...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            print("🔄 Обработка...")
            
            # Попытка распознавания через Google (бесплатно)
            try:
                text = self.recognizer.google_speech_to_text(
                    audio, 
                    language=self.language.split('-')[0]  # 'ru-RU' -> 'ru'
                )
                if text:
                    print(f"💬 Вы сказали: {text}")
                    return text.lower()
            except Exception as e:
                print(f"❌ Ошибка распознавания: {e}")
                
        except sr.WaitTimeoutError:
            print("⏰ Время ожидания истекло")
        except sr.UnknownValueError:
            print("❓ Не удалось распознать речь")
        except sr.RequestError as e:
            print(f"🌐 Ошибка сервиса: {e}")
        except Exception as e:
            print(f"⚠️ Неожиданная ошибка: {e}")
        
        return None
    
    def speak(self, text, use_offline=True):
        """
        Озвучивание текста
        
        Args:
            text: текст для озвучивания
            use_offline: использовать офлайн TTS (быстрее) или онлайн (качественнее)
        """
        if not text:
            return
        
        print(f"🔊 {Settings.ASSISTANT_NAME}: {text}")
        
        try:
            if use_offline:
                # Офлайн синтез (быстро, не требует интернета)
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # Онлайн синтез (качественнее, нужен интернет)
                tts = gTTS(text=text, lang=self.language.split('-')[0])
                
                # Сохранение во временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    tts.save(fp.name)
                    temp_path = fp.name
                
                playsound(temp_path)
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"❌ Ошибка синтеза речи: {e}")
            # Фоллбэк на печать
            print(text)
    
    def wake_word_detected(self, text):
        """Проверка наличия слова активации"""
        if not text:
            return False
        return Settings.WAKE_WORD in text.lower()
