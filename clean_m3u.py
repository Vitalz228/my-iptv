import os
import re
import urllib.request

# Прямая ссылка на твой плейлист
URL = "https://raw.githubusercontent.com/IPTVRU2026/IPTVMIR/main/IPTV_MEGA_PLAYLIST.m3u"
OUTPUT_FILE = "cleaned.m3u"

# Стоп-слова: всё это вырезается без пощады
STOP_WORDS = [
    r"\+\d", r"\(\+\d\)", r"timeshift", r"резерв", r"тест", r"test", r"offline",
    "самара", "уфа", "казань", "тюмень", "екатеринбург", "краснодар", "красноярск",
    "новосибирск", "владивосток", "хабаровск", "крым", "сочи", "питер", "спб",
    "нижний новгород", "челябинск", "пермь", "волгоград", "саратов", "иркутск",
    "кубань", "башкортостан", "татарстан", "дон-тр", "губерния", "армения", "беларусь"
]

CATEGORIES = {
    "Кино и Сериалы": [
        "кино", "film", "movie", "cinema", "tv1000", "vip", "fox", "amedia", 
        "дом кино", "иллюзион", "нст", "shot tv", "viju", "дорама", "сапфир", 
        "кинеко", "paramount", "комедия", "ужас", "сериал", "action", "драма"
    ],
    "Спорт": [
        "спорт", "sport", "матч", "футбол", "football", "eurosport", "кхл", 
        "khl", "ufc", "боец", "арена", "setanta", "хоккей", "mma", "бокс", "extreme"
    ],
    "Познавательные": [
        "discovery", "nat geo", "national geographic", "наука", "моя планета", 
        "history", "история", "viasat history", "animal planet", "живая планета", 
        "приключения", "tlc", "id extra", "охота", "рыбалка", "travel", "планета"
    ],
    "Детские": [
        "детск", "мульт", "карусель", "disney", "nickelodeon", "cartoon", 
        "nick", "ani", "tiji", "рыжий", "мультимузыка", "мультиландия"
    ],
    "Музыка": [
        "муз", "music", "mtv", "bridge", "ru.tv", "europa plus", "шансон", 
        "vh1", "mcm", "жара", "ля-минор"
    ],
    "Новости": [
        "новост", "news", "24", "rbc", "рбк", "euronews", "россия 24", 
        "cnn", "bbc", "dw", "известия"
    ],
    "Федеральные / Эфирные": [
        "первый канал", "россия 1", "нтв", "тнт", "стс", "пятница", 
        "рен тв", "тв-3", "тв 3", "звезда", "твц", "домашний", "че!", "спас", "отр", "мир"
    ],
    "18+": [
        "18+", "xxx", "porn", "adult", "hustler", "brazzers", "penthouse", 
        "playboy", "русская ночь", "blue hustler", "redlight"
    ]
}

def is_garbage(name):
    name_low = name.lower()
    for stop in STOP_WORDS:
        if re.search(stop, name_low):
            return True
    return False

def detect_category(name):
    name_low = name.lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in name_low:
                return category
    return "Разное"

def run():
    print(f"Качаю плейлист с GitHub (файл весит прилично, подожди секунд 10-20)...")
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Не удалось скачать: {e}")
        return

    lines = content.splitlines()
    print(f"Всего строк скачано: {len(lines)}. Начинаю фильтрацию...")

    seen_urls = set()
    cleaned_channels = []
    skipped_duplicates = 0
    skipped_trash = 0
    current_extinf = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            current_extinf = line
        elif not line.startswith("#") and current_extinf:
            url = line

            if url in seen_urls:
                skipped_duplicates += 1
                current_extinf = None
                continue

            channel_name = current_extinf.split(",")[-1].strip()

            if is_garbage(channel_name):
                skipped_trash += 1
                current_extinf = None
                continue

            category = detect_category(channel_name)

            # Проставляем категорию
            if 'group-title="' in current_extinf:
                current_extinf = re.sub(r'group-title="[^"]*"', f'group-title="{category}"', current_extinf)
            else:
                current_extinf = re.sub(r'(#EXTINF:-?\d+)', rf'\1 group-title="{category}"', current_extinf)

            seen_urls.add(url)
            cleaned_channels.append((category, current_extinf, url))
            current_extinf = None

    # Сортировка по категориям
    cleaned_channels.sort(key=lambda x: x[0])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, extinf, url in cleaned_channels:
            f.write(f"{extinf}\n{url}\n")

    print("\nОбработка завершена успешно!")
    print(f"-> Вырезано дубликатов: {skipped_duplicates}")
    print(f"-> Вырезано регионов/мусора: {skipped_trash}")
    print(f"-> Отобрано чистых каналов: {len(cleaned_channels)}")
    print(f"-> Файл сохранен в: {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
