"""
Модуль интеграции с ИИ-моделями (LLM)
Поддержка: OpenAI GPT, Google Gemini, заглушка для локальных моделей
"""
import openai
from config.settings import Settings


class AIBrain:
    """Интеллектуальное ядро ассистента"""
    
    def __init__(self):
        self.openai_client = None
        self.use_google = False
        
        if Settings.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=Settings.OPENAI_API_KEY)
            print("✅ OpenAI инициализирован")
        
        # Можно добавить поддержку Google Gemini и других моделей
    
    def think(self, user_message, context=None):
        """
        Получение ответа от ИИ-модели
        
        Args:
            user_message: сообщение пользователя
            context: контекст диалога (список предыдущих сообщений)
            
        Returns:
            str: ответ ИИ
        """
        if not Settings.is_configured():
            return self._simple_response(user_message)
        
        # Формирование системного промпта
        system_prompt = f"""Ты - {Settings.ASSISTANT_NAME}, персональный ИИ-ассистент, 
вдохновленный Джарвисом из Железного Человека.

Твои характеристики:
- Умен, остроумен и немного саркастичен
- Говоришь кратко и по делу
- Всегда готов помочь
- Используй эмодзи умеренно
- Отвечай на русском языке

Будь полезен, дружелюбен и эффективен."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавление контекста если есть
        if context:
            messages.extend(context[-10:])  # Последние 10 сообщений
        
        # Добавление текущего сообщения
        messages.append({"role": "user", "content": user_message})
        
        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",  # или gpt-4
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Ошибка ИИ: {e}")
            return self._simple_response(user_message)
    
    def _simple_response(self, message):
        """
        Простые ответы без использования API (режим без ключей)
        """
        message_lower = message.lower()
        
        responses = {
            'привет': f"Здравствуйте! Я {Settings.ASSISTANT_NAME}, готов к работе! 🤖",
            'здравствуй': f"Приветствую! Чем могу помочь? ✨",
            'как дела': "Все системы в норме! Готов выполнять задачи! 💪",
            'кто ты': f"Я {Settings.ASSISTANT_NAME}, ваш персональный ассистент. Пока работаю в базовом режиме.",
            'что умеешь': "Пока умею немного: слушать команды, говорить, показывать время и погоду. Но я учусь! 📚",
            'спасибо': "Всегда пожалуйста! 😊",
            'пока': "До связи! Буду ждать новых команд! 👋",
        }
        
        for key, response in responses.items():
            if key in message_lower:
                return response
        
        return "Извините, пока я не могу ответить на этот вопрос без подключения к ИИ-модели. Добавьте API ключ для полной функциональности."
    
    def get_context_message(self, role, content):
        """Создание сообщения для контекста"""
        return {"role": role, "content": content}
