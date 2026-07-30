"""
Главный файл запуска ассистента JARVIS
"""
import sys
import os

# Добавление корневой директории в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from modules.speech import VoiceManager
from modules.brain import AIBrain
from modules.commands import CommandHandler


class JarvisAssistant:
    """Основной класс ассистента"""
    
    def __init__(self):
        print(f"\n{'='*50}")
        print(f"🚀 Инициализация {Settings.ASSISTANT_NAME}...")
        print(f"{'='*50}\n")
        
        # Инициализация компонентов
        self.voice = None
        self.brain = AIBrain()
        self.commands = CommandHandler()
        
        # Контекст диалога
        self.context = []
        
        # Флаг работы
        self.running = True
        
        # Проверка конфигурации
        if not Settings.is_configured():
            print("⚠️  ВНИМАНИЕ: API ключи не настроены!")
            print("   Для полной функциональности добавьте ключи в .env файл\n")
        
        try:
            self.voice = VoiceManager()
        except Exception as e:
            print(f"⚠️  Микрофон недоступен: {e}")
            print("   Работа будет в текстовом режиме\n")
    
    def greet(self):
        """Приветствие при запуске"""
        greeting = f"{Settings.ASSISTANT_NAME} активирован и готов к работе! Чем могу помочь?"
        
        if self.voice:
            self.voice.speak(greeting)
        else:
            print(f"🔊 {greeting}")
    
    def process_command(self, text):
        """Обработка полученной команды"""
        if not text:
            return
        
        # Проверка на встроенные команды
        success, response = self.commands.execute(text)
        
        if success:
            if response == "stop_signal":
                self.running = False
                return
            
            if self.voice:
                self.voice.speak(response)
            else:
                print(f"🔊 {response}")
            return
        
        # Если команда не распознана - отправляем в ИИ
        self.context.append(self.brain.get_context_message("user", text))
        
        ai_response = self.brain.think(text, self.context)
        
        # Сохранение ответа в контекст
        self.context.append(self.brain.get_context_message("assistant", ai_response))
        
        if self.voice:
            self.voice.speak(ai_response)
        else:
            print(f"🔊 {ai_response}")
    
    def run_voice_mode(self):
        """Запуск в голосовом режиме"""
        self.greet()
        
        print("\n🎤 Голосовой режим активирован")
        print(f"   Скажите '{Settings.WAKE_WORD}' для активации")
        print("   или 'помощь' для списка команд\n")
        
        wake_mode = False  # Режим ожидания слова активации
        
        while self.running:
            try:
                # Если не в режиме активации - ждем слово активации
                if not wake_mode:
                    text = self.voice.listen(timeout=3)
                    
                    if text and self.voice.wake_word_detected(text):
                        wake_mode = True
                        activation_phrase = f"Да, сэр? Слушаю внимательно."
                        self.voice.speak(activation_phrase)
                    continue
                
                # В режиме активации - слушаем команду
                text = self.voice.listen(timeout=5, phrase_time_limit=10)
                
                if text:
                    # Проверка на деактивацию
                    if 'отбой' in text or 'пока' in text:
                        wake_mode = False
                        self.voice.speak("Хорошо, сэр. Буду на связи.")
                        continue
                    
                    self.process_command(text)
                    wake_mode = False
                    
            except KeyboardInterrupt:
                print("\n\n👋 Завершение работы по команде пользователя")
                self.running = False
            except Exception as e:
                print(f"⚠️  Ошибка: {e}")
                continue
    
    def run_text_mode(self):
        """Запуск в текстовом режиме (без микрофона)"""
        self.greet()
        
        print("\n💬 Текстовый режим")
        print("   Вводите команды текстом")
        print("   'выход' для завершения\n")
        
        while self.running:
            try:
                text = input("\nВы: ").strip()
                
                if not text:
                    continue
                
                if text.lower() in ['выход', 'стоп', 'quit', 'exit']:
                    self.running = False
                    break
                
                self.process_command(text)
                
            except KeyboardInterrupt:
                print("\n\n👋 Завершение работы")
                self.running = False
            except EOFError:
                self.running = False
    
    def run(self):
        """Запуск ассистента"""
        if self.voice:
            self.run_voice_mode()
        else:
            self.run_text_mode()
        
        # Прощание
        farewell = "До свидания, сэр! Был рад помочь!"
        
        if self.voice:
            self.voice.speak(farewell)
        else:
            print(f"🔊 {farewell}")


def main():
    """Точка входа"""
    assistant = JarvisAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
