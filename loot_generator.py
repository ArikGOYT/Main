import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin, urlparse

BASE_URL = "https://2e.aonprd.com/"
EQUIPMENT_URL = urljoin(BASE_URL, "Equipment.aspx")

# API endpoint для поиска предметов (используется внутренним виджетом сайта)
API_URL = "https://2e.aonprd.com/api/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Referer": EQUIPMENT_URL
}

# Кэширование запросов для избежания повторных загрузок
_url_cache = {}

def get_soup(url):
    """Скачивает страницу и возвращает BeautifulSoup объект."""
    if url in _url_cache:
        return _url_cache[url]
    
    print(f"Загрузка: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8' 
        soup = BeautifulSoup(response.text, 'html.parser')
        _url_cache[url] = soup
        return soup
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
        return None

def fetch_items_from_api(category_id=None, min_level=1, max_level=20, limit=50):
    """
    Получает список предметов через внутренний API сайта.
    """
    print("Запрос к API предметов...")
    
    # Параметры запроса
    params = {
        "query": "*",
        "type": "equipment",
        "display": "table",
        "columns": "name,level,price,rarity,traits,item_category,url",
        "sort": "level-asc",
        "limit": limit
    }
    
    if category_id:
        params["category"] = str(category_id)
    
    try:
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        items = []
        for item in data.get("results", []):
            level = item.get("level", 0)
            if min_level <= level <= max_level:
                items.append({
                    "name": item.get("name", "Unknown"),
                    "level": level,
                    "price_gp": parse_price_string(item.get("price", "0")),
                    "url": urljoin(BASE_URL, item.get("url", "")),
                    "rarity": item.get("rarity", ""),
                    "traits": item.get("traits", []),
                    "category": item.get("item_category", "")
                })
        
        print(f"Найдено предметов через API: {len(items)}")
        return items
        
    except Exception as e:
        print(f"Ошибка API: {e}")
        return []

def parse_price_string(price_text):
    """Превращает строку цены в число золотых монет."""
    if not price_text:
        return 0.0
    
    # Удаляем всё кроме цифр, точек и запятых
    clean_text = re.sub(r'[^\d.,]', '', str(price_text))
    clean_text = clean_text.replace(',', '')
    
    try:
        return float(clean_text)
    except ValueError:
        return 0.0

def parse_item_details(item_url):
    """Заходит на страницу предмета и вытаскивает детали."""
    soup = get_soup(item_url)
    if not soup:
        return None

    # Название
    title_tag = soup.find("h1", {"class": "title"})
    name = title_tag.get_text(strip=True) if title_tag else "Unknown"

    # Уровень
    level = 0
    text_content = soup.get_text()
    
    level_match = re.search(r'Item\s+(\d+)', text_content)
    if level_match:
        level = int(level_match.group(1))
    else:
        level_matches = re.findall(r'Level\s+(\d+)', text_content)
        if level_matches:
            level = int(level_matches[0])

    # Цена
    price = 0.0
    price_label = soup.find(string=re.compile(r"^Price\s*", re.IGNORECASE))
    if price_label:
        parent = price_label.find_parent()
        if parent:
            price_text = parent.get_text(separator=" ", strip=True)
            money_match = re.search(r'([\d,]+)\s*(gp|sp|cp)', price_text, re.IGNORECASE)
            if money_match:
                val = parse_price(money_match.group(1))
                unit = money_match.group(2).lower()
                if unit == 'sp':
                    val /= 10
                elif unit == 'cp':
                    val /= 100
                price = val

    # Описание
    content_div = soup.find("div", {"class": "content"})
    description = ""
    if content_div:
        paragraphs = content_div.find_all("p")
        description = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

    return {
        "name": name,
        "level": level,
        "price_gp": round(price, 2),
        "url": item_url,
        "description": description[:500] + "..." if len(description) > 500 else description
    }

def parse_price(price_text):
    """Превращает строку цены (напр. '1,200 gp') в число золотых монет (float)."""
    if not price_text:
        return 0.0
    
    clean_text = re.sub(r'[^\d.,]', '', price_text)
    clean_text = clean_text.replace(',', '')
    
    try:
        return float(clean_text)
    except ValueError:
        return 0.0

def generate_loot(min_level=1, max_level=20, target_value=None, count=5):
    """
    Генерирует список лута.
    Сначала пытается загрузить из локальной базы, потом парсит сайт.
    """
    # 1. Пробуем загрузить из локального JSON файла
    all_items = load_items_from_json()
    
    if not all_items:
        print("Локальная база не найдена, пробуем API...")
        all_items = fetch_items_from_api(
            min_level=min_level,
            max_level=max_level,
            limit=100
        )
    
    if not all_items:
        print("Не удалось получить предметы, используем демо-данные...")
        # Демо-данные для теста
        all_items = [
            {"name": "Bag of Holding", "level": 3, "price_gp": 60, "category": "Worn Items"},
            {"name": "Cloak of Elvenkind", "level": 4, "price_gp": 85, "category": "Worn Items"},
            {"name": "Alchemist's Fire", "level": 1, "price_gp": 4, "category": "Alchemical Items"},
            {"name": "Elixir of Life", "level": 1, "price_gp": 4, "category": "Alchemical Items"},
            {"name": "Healer's Tools", "level": 0, "price_gp": 5, "category": "Adventuring Gear"},
            {"name": "Potency Rune +1", "level": 4, "price_gp": 70, "category": "Runes"},
            {"name": "Potion of Healing", "level": 1, "price_gp": 4, "category": "Consumables"},
        ]

    # Фильтруем по уровню
    filtered_items = [i for i in all_items if min_level <= i.get('level', 0) <= max_level]
    print(f"Всего найдено предметов: {len(filtered_items)}")

    # Логика генерации
    generated_loot = []
    
    if target_value:
        current_value = 0
        available_items = [i for i in filtered_items if i.get('price_gp', 0) > 0]
        available_items.sort(key=lambda x: x['price_gp'], reverse=True)
        
        while current_value < target_value and available_items:
            found = False
            for i, item in enumerate(available_items):
                if current_value + item['price_gp'] <= target_value * 1.1:
                    generated_loot.append(item)
                    current_value += item['price_gp']
                    available_items.pop(i)
                    found = True
                    break
            
            if not found:
                break
                
    else:
        import random
        if filtered_items:
            generated_loot = random.sample(filtered_items, min(count, len(filtered_items)))

    return generated_loot

def load_items_from_json(filename="loot_database.json"):
    """Загружает предметы из локального JSON файла."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items = data.get("items", [])
            print(f"Загружено {len(items)} предметов из {filename}")
            return items
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return []

if __name__ == "__main__":
    print("--- Генератор лута Pathfinder 2e ---")
    
    # Пример использования:
    # 1. Получить 5 случайных магических предметов 5-10 уровня
    # loot = generate_loot(min_level=5, max_level=10, count=5)
    
    # 2. Подобрать лут на сумму ~1000 золотых
    loot = generate_loot(target_value=1000)
    
    print("\n--- Результат ---")
    total_val = 0
    for item in loot:
        print(f"[Lvl {item['level']}] {item['name']} - {item['price_gp']} gp")
        total_val += item['price_gp']
    
    print(f"\nИтого стоимость: {total_val:.2f} gp")
    
    # Сохранение в JSON
    with open("generated_loot.json", "w", encoding="utf-8") as f:
        json.dump(loot, f, ensure_ascii=False, indent=2)
    
    print("\nДанные сохранены в generated_loot.json")
