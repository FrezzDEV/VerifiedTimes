from telethon import TelegramClient
import asyncio
import re
from datetime import datetime, time

# Настройки
api_id = 23937071  # Ваш API ID
api_hash = "d4abf89f2ff12e2f9c2b35035b4f8e86"  # Ваш API Hash
CHAT_ID = -1002031799801  # ID чата канала
CHECK_INTERVAL = 5  # Проверять каждые 5 минут (в секундах)

# Регулярные выражения
TRIGGER_PATTERN = re.compile(r'^50 000 пп за 325.*кто возьмет заказ\?.*❌', re.IGNORECASE)
CONFIRM_PATTERN = re.compile(r'✅✅✅\.?$')  # С точкой или без в конце

# Тексты ответов
WARNING_REPLY = "Я"
CONFIRM_REPLY = "✅ Подтверждаю получение!"

# Время "тишины" (не отвечаем с 23:00 до 8:00)
QUIET_HOURS_START = time(23, 0)
QUIET_HOURS_END = time(10, 0)

# Храним ID сообщений, на которые уже ответили
answered_messages = set()

def is_quiet_time():
    """Проверяем, сейчас время 'тишины' (не отвечаем)"""
    now = datetime.now().time()
    return QUIET_HOURS_START <= now or now < QUIET_HOURS_END

async def check_messages(client):
    try:
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"\n{current_time} Проверяю новые сообщения...")
        
        # Получаем последние 20 сообщений
        async for message in client.iter_messages(CHAT_ID, limit=20):
            # Пропускаем, если уже отвечали
            if message.id in answered_messages:
                continue
                
            # Проверка на подтверждение (✅✅✅)
            if message.text and CONFIRM_PATTERN.search(message.text):
                print(f"🔔 Найдено подтверждение: {message.text}")
                await client.send_message(
                    CHAT_ID,
                    CONFIRM_REPLY,
                    reply_to=message.id
                )
                answered_messages.add(message.id)
                continue
                
            # Проверка основного триггера (только не в "тихие" часы)
            if not is_quiet_time() and message.text and TRIGGER_PATTERN.search(message.text):
                print(f"🔍 Найдено целевое сообщение: {message.text[:60]}...")
                
                # Проверяем, есть ли наши ответы
                replied = False
                async for reply in client.iter_messages(
                    CHAT_ID,
                    reply_to=message.id,
                    from_user="me"
                ):
                    replied = True
                    break
                
                if not replied:
                    print("💬 Отвечаю с предупреждением...")
                    await client.send_message(
                        CHAT_ID,
                        WARNING_REPLY,
                        reply_to=message.id
                    )
                    answered_messages.add(message.id)
                else:
                    print("⏩ Уже отвечал, пропускаю")
                    answered_messages.add(message.id)
                    
    except Exception as e:
        print(f"⚠️ Ошибка: {str(e)}")

async def main():
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start()
    
    print("🔍 Бот запущен. Мониторю чат...")
    print(f"⏰ Режим 'тишины' с {QUIET_HOURS_START.strftime('%H:%M')} до {QUIET_HOURS_END.strftime('%H:%M')}")
    
    # Бесконечный цикл проверки
    while True:
        await check_messages(client)
        await asyncio.sleep(CHECK_INTERVAL)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n🛑 Скрипт остановлен")