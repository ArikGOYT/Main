"""
Модуль обработки команд
Встроенные команды для управления системой и получения информации
"""
import datetime
import subprocess
import platform
from config.settings import Settings


class CommandHandler:
    """Обработчик встроенных команд"""
    
    def __init__(self):
        self.commands = {
            'время': self.get_time,
            'дата': self.get_date,
            'погода': self.get_weather_stub,
            'система': self.get_system_info,
            'помощь': self.show_help,
            'стоп': self.stop_assistant,
            'выход': self.stop_assistant,
        }
    
    def execute(self, command):
        """
        Выполнение команды
        
        Args:
            command: текст команды
            
        Returns:
            tuple: (success: bool, response: str)
        """
        if not command:
            return False, "Команда не распознана"
        
        command_lower = command.lower()
        
        # Проверка на встроенные команды
        for cmd_name, cmd_func in self.commands.items():
            if cmd_name in command_lower:
                try:
                    return True, cmd_func(command)
                except Exception as e:
                    return False, f"Ошибка при выполнении: {e}"
        
        # Команда не найдена
        return False, None
    
    def get_time(self, _):
        """Показать текущее время"""
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S")
        return f"Сейчас {time_str} 🕐"
    
    def get_date(self, _):
        """Показать текущую дату"""
        now = datetime.datetime.now()
        date_str = now.strftime("%d.%m.%Y, %A")
        return f"Сегодня {date_str} 📅"
    
    def get_weather_stub(self, _):
        """Заглушка для погоды (можно расширить через API)"""
        return "Погодный модуль требует настройки API. Попробуйте позже! 🌤️"
    
    def get_system_info(self, _):
        """Информация о системе"""
        system = platform.system()
        processor = platform.processor()
        python_version = platform.python_version()
        
        return f"""Система: {system}
Процессор: {processor}
Python: {python_version}
Имя ассистента: {Settings.ASSISTANT_NAME} 💻"""
    
    def show_help(self, _):
        """Показать доступные команды"""
        return """Доступные команды:
- Время / Который час - показать время
- Дата - показать дату
- Погода - узнать погоду
- Система - информация о системе
- Помощь - этот список
- Стоп / Выход - завершить работу

Также вы можете задавать вопросы - я постараюсь ответить! 🤖"""
    
    def stop_assistant(self, _):
        """Остановка ассистента"""
        return "stop_signal"
