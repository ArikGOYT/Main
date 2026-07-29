import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin

BASE_URL = "https://pf2.ru"
START_URL = "https://pf2.ru/equipment"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
}

def get_soup(url):
    """Скачивает страницу и возвращает BeautifulSoup объект."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
        return None

def parse_price(price_str):
    """Преобразует строку цены (напр. '10 зм', '5 см 2 мм') в числовое значение в медных монетах (мм)."""
    if not price_str:
        return 0
    
    price_str = price_str.lower().replace(',', '.').strip()
    
    # Если цена просто числом или с точкой (редко, но бывает)
    try:
        return int(float(price_str) * 100) # Допустим, это золото сразу? Нет, лучше парсить суффиксы
    except ValueError:
        pass

    total_copper = 0
    
    # Паттерны для золота (зм/gp), серебра (см/sp), меди (мм/cp)
    # Примеры: "10 зм", "5 см 2 мм", "1 зм 5 см"
    
    # Золото
    match_gp = re.search(r'(\d+(?:\.\d+)?)\s*(?:зм|gp|зол)', price_str)
    if match_gp:
        total_copper += int(float(match_gp.group(1)) * 100)
        
    # Серебро
    match_sp = re.search(r'(\d+(?:\.\d+)?)\s*(?:см|sp|сер)', price_str)
    if match_sp:
        total_copper += int(float(match_sp.group(1)) * 10)
        
    # Медь
    match_cp = re.search(r'(\d+(?:\.\d+)?)\s*(?:мм|cp|мед)', price_str)
    if match_cp:
        total_copper += int(float(match_cp.group(1)))
        
    # Если ничего не найдено, но есть число, предположим, что это золото (частый случай в кратких таблицах)
    if total_copper == 0:
        match_num = re.search(r'(\d+(?:\.\d+)?)', price_str)
        if match_num:
            # Проверим, нет ли рядом обозначений, если нет - считаем золотом для безопасности или 0
            # В pf2.ru часто пишут просто "10" если это золото в некоторых таблицах, но лучше 0 если не ясно
            pass 
            
    return total_copper

def parse_item_page(url):
    """Парсит страницу конкретного предмета."""
    soup = get_soup(url)
    if not soup:
        return None

    # Название обычно в h1
    title_tag = soup.find('h1')
    name = title_tag.get_text(strip=True) if title_tag else "Без названия"

    # Уровень и цена часто находятся в блоке свойств перед описанием
    # На pf2.ru структура может быть разной, попробуем найти таблицу свойств или div с классом
    level = 0
    price_raw = "0"
    
    # Ищем блоки с информацией. Часто это div.item-details или similar
    # Попробуем найти текст "Уровень" и "Цена" в содержимом
    
    content_text = soup.get_text()
    
    # Поиск уровня (часто формат: "Уровень X" или "Level X")
    level_match = re.search(r'уровень\s*(\d+)', content_text, re.IGNORECASE)
    if level_match:
        level = int(level_match.group(1))
    else:
        # Иногда уровень в заголовке или классе
        # Попытка найти в первом абзаце или dl/dt/dd
        details_div = soup.find('div', class_='item-details') or soup.find('div', class_='content')
        if details_div:
            # Ищем dt/dd пары
            dts = details_div.find_all('dt')
            for dt in dts:
                text = dt.get_text(strip=True).lower()
                dd = dt.find_next_sibling('dd')
                if dd:
                    val = dd.get_text(strip=True)
                    if 'уровень' in text:
                        m = re.search(r'(\d+)', val)
                        if m: level = int(m.group(1))
                    if 'цена' in text or 'cost' in text:
                        price_raw = val

    # Если цена не найдена в деталях, ищем в первом абзаце описания часто пишут "Цена: ..."
    if price_raw == "0":
        price_match = re.search(r'[Цц]ена[:\s]*([^\n;]+)', content_text)
        if price_match:
            price_raw = price_match.group(1)

    price_value = parse_price(price_raw)
    
    # Описание (берем первый большой параграф после заголовка или специфический блок)
    description = ""
    desc_div = soup.find('div', class_='description') or soup.find('div', class_='text')
    if desc_div:
        description = desc_div.get_text(strip=True)[:500] # Берем первые 500 символов
    else:
        #fallback к первому p после h1
        h1 = soup.find('h1')
        if h1:
            for sibling in h1.next_siblings:
                if hasattr(sibling, 'name') and sibling.name == 'p':
                    description = sibling.get_text(strip=True)[:500]
                    break

    return {
        "name": name,
        "level": level,
        "price_raw": price_raw.strip(),
        "price_copper": price_value,
        "url": url,
        "description": description
    }

def main():
    print(f"Начинаем парсинг с {START_URL}...")
    soup = get_soup(START_URL)
    if not soup:
        return

    item_links = set()
    
    # 1. Собираем ссылки на предметы
    # Стратегия: ищем ссылки, ведущие на /equipment/... но не на категории
    # Обычно список предметов находится в ul/li или таблице
    
    # Пробуем найти все ссылки внутри основного контента
    content_area = soup.find('main') or soup.find('div', class_='content') or soup.body
    
    if content_area:
        links = content_area.find_all('a', href=True)
        for link in links:
            href = link['href']
            full_url = urljoin(BASE_URL, href)
            
            # Фильтр: ссылка должна вести на страницу предмета
            # Избегаем якорей, категорий и внешних ссылок
            if BASE_URL in full_url and '/equipment/' in full_url:
                # Исключаем саму страницу списка и пагинацию
                if full_url == START_URL or 'page=' in full_url:
                    continue
                # Эвристика: если в ссылке есть последний слэш и после него что-то, или это не конец строки
                # На pf2.ru URL предметов обычно выглядят как https://pf2.ru/equipment/weapons/sword
                # Или просто https://pf2.ru/equipment/item-name
                
                # Добавляем, если ссылка выглядит достаточно уникальной (не просто /equipment/)
                if full_url.count('/') > 3: 
                    item_links.add(full_url)
    
    # Если ссылок мало, возможно, они подгружаются JS или структура другая.
    # Попробуем альтернативу: поиск по всем ссылкам на странице, содержащим слова
    if len(item_links) < 5:
        print("Мало ссылок найдено стандартным методом, пробуем расширенный поиск...")
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            text = link.get_text(strip=True).lower()
            href = link['href']
            # Если ссылка ведет внутрь и текст похож на название предмета (не "каталог", "главная")
            if href.startswith('/equipment/') and len(text) > 2 and text not in ['снаряжение', 'оружие', 'броня', 'все']:
                 full_url = urljoin(BASE_URL, href)
                 if full_url != START_URL:
                     item_links.add(full_url)

    print(f"Найдено потенциальных предметов: {len(item_links)}")
    
    database = []
    
    # 2. Проходим по каждому предмету
    for i, url in enumerate(item_links):
        print(f"[{i+1}/{len(item_links)}] Парсим: {url}")
        data = parse_item_page(url)
        if data:
            database.append(data)
        time.sleep(0.5) # Вежливость к серверу
        
    # 3. Сохраняем результат
    output_file = 'pf2_loot_database.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
        
    print(f"\nГотово! Сохранено {len(database)} предметов в файл {output_file}")
    
    # Статистика
    if database:
        levels = [item['level'] for item in database]
        print(f"Диапазон уровней: {min(levels)} - {max(levels)}")
        print(f"Пример предмета: {database[0]['name']} (Ур. {database[0]['level']}, Цена: {database[0]['price_raw']})")

if __name__ == "__main__":
    main()