import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin

BASE_URL = "https://2e.aonprd.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL
}

def get_soup(url):
    """Получает HTML страницы и возвращает BeautifulSoup объект."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе {url}: {e}")
        return None

def parse_price(price_str):
    """Конвертирует строку цены (напр. '1 gp', '5 sp') в золотые монеты (float)."""
    if not price_str or price_str == "—":
        return 0.0
    
    price_str = price_str.lower().replace(",", "")
    total_gp = 0.0
    
    # Паттерны для поиска чисел и валют
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*gp', 1),
        (r'(\d+(?:\.\d+)?)\s*sp', 0.1),
        (r'(\d+(?:\.\d+)?)\s*cp', 0.01),
        (r'(\d+(?:\.\d+)?)\s*pp', 10)
    ]
    
    found = False
    for pattern, multiplier in patterns:
        match = re.search(pattern, price_str)
        if match:
            total_gp += float(match.group(1)) * multiplier
            found = True
            
    if not found:
        # Пробуем найти просто число, если валюта не указана явно (редко, но бывает)
        match = re.search(r'(\d+(?:\.\d+)?)', price_str)
        if match:
            return float(match.group(1))
            
    return total_gp

def extract_item_details(item_url):
    """Заходит на страницу предмета и вытаскивает детали."""
    soup = get_soup(item_url)
    if not soup:
        return None

    # Название
    title_tag = soup.find("h1", class_="detailtitle")
    if not title_tag:
        return None
    name = title_tag.get_text(strip=True)

    # Уровень и цена часто в одном блоке рядом с названием или в h2/h3
    # Обычно структура: <h2>Item Name</h2> <div class="detailtitle">...Level X; Price Y...</div>
    # Или в самом верху в блоке свойств
    
    level = 0
    price_str = "0 gp"
    
    # Ищем блок с характеристиками (обычно сразу после заголовка)
    # На aonprd это часто div с классом 'detailtitle' или соседние параграфы
    detail_div = soup.find("div", class_="detailtitle")
    if detail_div:
        text_content = detail_div.get_text()
        
        # Поиск уровня
        level_match = re.search(r'Item\s+(\d+)', text_content, re.IGNORECASE)
        if level_match:
            level = int(level_match.group(1))
        else:
            # Иногда просто "Level X"
            level_match = re.search(r'Level\s+(\d+)', text_content, re.IGNORECASE)
            if level_match:
                level = int(level_match.group(1))

        # Поиск цены
        price_match = re.search(r'Price\s+([^;]+?)(?:;|$)', text_content, re.IGNORECASE)
        if price_match:
            price_str = price_match.group(1).strip()
    
    price_gp = parse_price(price_str)

    # Описание (все текстовые блоки после заголовков, игнорируя навигацию)
    description_parts = []
    content_div = soup.find("div", class_="detailcontent")
    if content_div:
        # Берем текст, убираем лишние пробелы
        desc_text = content_div.get_text(separator=" ", strip=True)
        description_parts.append(desc_text)
    
    # Если detailcontent не найден, пробуем собрать из параграфов после заголовка
    if not description_parts:
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 20: # Фильтр коротких строк
                description_parts.append(text)

    full_description = " ".join(description_parts)[:2000] # Ограничим длину

    return {
        "name": name,
        "level": level,
        "price_raw": price_str,
        "price_gp": price_gp,
        "url": item_url,
        "description": full_description
    }

def get_equipment_categories():
    """Парсит главную страницу Equipment и находит ссылки на категории."""
    url = urljoin(BASE_URL, "Equipment.aspx")
    soup = get_soup(url)
    if not soup:
        return []

    categories = []
    # Ищем ссылки в основном контенте. Обычно они в списке ul или таблице
    # Структура AONPRD: ссылки находятся в блоке с классом 'listbox' или просто в контенте
    
    content_area = soup.find("div", class_="listbox") or soup.find("div", class_="content")
    if not content_area:
        # Если стандартные классы не найдены, ищем все ссылки, содержащие 'Equipment'
        links = soup.find_all("a", href=True)
        for link in links:
            href = link['href']
            if 'Equipment' in href and 'aspx' in href and href != "Equipment.aspx":
                text = link.get_text(strip=True)
                if text:
                    categories.append({"name": text, "url": urljoin(BASE_URL, href)})
        return list({v['url']:v for v in categories}.values()) # Удаление дублей

    links = content_area.find_all("a", href=True)
    for link in links:
        href = link['href']
        text = link.get_text(strip=True)
        if text and 'aspx' in href:
            categories.append({
                "name": text,
                "url": urljoin(BASE_URL, href)
            })
            
    return categories

def parse_category(category_url):
    """Парсит страницу категории и возвращает списки ссылок на предметы."""
    soup = get_soup(category_url)
    if not soup:
        return []

    items = []
    # На AONPRD предметы обычно перечислены ссылками в теле страницы
    # Часто внутри div с классом 'listbox' или просто списком
    
    # Ищем все ссылки, которые ведут на страницы предметов (содержат ID или специфичный паттерн)
    # Обычно ссылки выглядят как Items.aspx?ID=123
    
    links = soup.find_all("a", href=True)
    for link in links:
        href = link['href']
        text = link.get_text(strip=True)
        
        # Фильтр: ссылка должна вести на детальную страницу предмета
        # Паттерн: содержит 'Items.aspx' или 'Equipment.aspx' с параметрами, но не сама категория
        if ('Items.aspx' in href or 'Equipment.aspx' in href) and '=' in href:
             if text and text != "Next" and text != "Previous": # Исключаем пагинацию
                items.append({
                    "name": text,
                    "url": urljoin(BASE_URL, href)
                })
    
    return items

def main():
    print("🔍 Начинаем парсинг aonprd.com...")
    
    # 1. Получаем категории
    print("📂 Сканирование категорий оборудования...")
    categories = get_equipment_categories()
    
    if not categories:
        print("❌ Не удалось найти категории. Проверьте структуру сайта или подключение.")
        # Попробуем хардкодные ссылки на всякий случай, если парсер категорий не сработал
        print("⚠️ Попытка использования известных категорий...")
        categories = [
            {"name": "Weapons", "url": urljoin(BASE_URL, "Equipment.aspx?Category=Weapons")},
            {"name": "Armor", "url": urljoin(BASE_URL, "Equipment.aspx?Category=Armor")},
            {"name": "Adventuring Gear", "url": urljoin(BASE_URL, "Equipment.aspx?Category=AdventuringGear")}
        ]

    all_items = []
    
    # 2. Проходим по категориям
    for i, cat in enumerate(categories):
        print(f"[{i+1}/{len(categories)}] Категория: {cat['name']}")
        
        items_in_cat = parse_category(cat['url'])
        print(f"   Найдено ссылок: {len(items_in_cat)}")
        
        # 3. Проходим по предметам в категории
        for j, item_link in enumerate(items_in_cat):
            # Ограничим количество предметов для теста, если нужно (убрать комментарий для продакшена)
            # if j > 5: break 
            
            print(f"   ➤ Парсинг: {item_link['name']}...", end="\r")
            
            details = extract_item_details(item_link['url'])
            if details:
                all_items.append(details)
            
            # Вежливая задержка
            time.sleep(0.5)
        
        print(f"   ✅ Категория завершена.")
        time.sleep(1) # Задержка между категориями

    # Сохранение
    output_file = "aonprd_loot_database.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 Готово! Сохранено {len(all_items)} предметов в файл {output_file}")
    
    # Вывод статистики
    if all_items:
        avg_price = sum(i['price_gp'] for i in all_items) / len(all_items)
        max_level = max(i['level'] for i in all_items)
        print(f"📊 Средняя цена: {avg_price:.2f} gp")
        print(f"📊 Максимальный уровень: {max_level}")

if __name__ == "__main__":
    main()
