"""
Модуль напоминаний и таймеров
"""
import datetime
import schedule
import threading
import time


class ReminderModule:
    """Модуль управления напоминаниями"""
    
    def __init__(self):
        self.reminders = []
        self.running = False
    
    def start_scheduler(self):
        """Запуск планировщика в фоне"""
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def add_reminder(self, message, delay_minutes=0, specific_time=None):
        """
        Добавление напоминания
        
        Args:
            message: текст напоминания
            delay_minutes: задержка в минутах
            specific_time: конкретное время (datetime.time)
            
        Returns:
            str: подтверждение
        """
        if specific_time:
            schedule.every().day.at(specific_time.strftime("%H:%M")).do(
                self._trigger_reminder, message
            )
            return f"Напоминание установлено на {specific_time.strftime('%H:%M')}: {message}"
        elif delay_minutes > 0:
            schedule.every(delay_minutes).minutes.do(
                self._trigger_reminder, message
            ).tag('once')
            return f"Напоминание через {delay_minutes} мин: {message}"
        else:
            return "Укажите время или задержку для напоминания"
    
    def _trigger_reminder(self, message):
        """Срабатывание напоминания"""
        print(f"\n🔔 НАПОМИНАНИЕ: {message}")
        # Здесь можно добавить голосовое озвучивание
        return message
    
    def stop_scheduler(self):
        """Остановка планировщика"""
        self.running = False
        schedule.clear()
