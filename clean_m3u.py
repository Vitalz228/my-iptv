import os
import re
import urllib.request

URL = "https://raw.githubusercontent.com/IPTVRU2026/IPTVMIR/main/IPTV_MEGA_PLAYLIST.m3u"
OUTPUT_FILE = "cleaned.m3u"

# 1. ЧАСОВЫЕ ПОЯСА И ТЕХНИЧЕСКИЙ МУСОР
GARBAGE_PATTERNS = [
    r"\+\d", r"\(\+\d\)", r"timeshift", r"резерв", r"тест", r"test", 
    r"offline", r"заглушка", r"инфоканал", r"promo", r"промо"
]

# 2. ВЗРОСЛЫЕ КАНАЛЫ (18+)
ADULT_PATTERNS = [
    r"18\+", r"xxx", r"porn", r"adult", r"hustler", r"brazzers", r"penthouse",
    r"playboy", r"русская ночь", r"blue hustler", r"redlight", r"erox", r"dorcel",
    r"nuart", r"babes", r"candy", r"exotic", r"passion", r"эротика", r"эротик",
    r"эро", r"sex", r"секс", r"private", r"о-ля-ля", r"o-la-la", r"nightman"
]

# 3. УЗБЕКСКИЕ КАНАЛЫ
UZBEK_PATTERNS = [
    r"узбек", r"uzbek", r"uzb", r"ташкент", r"toshkent", r"самарканд", r"samarqand",
    r"sevimli", r"zo'r", r"zor tv", r"my5", r"milliy", r"dunyo", r"yoshlar", 
    r"navo", r"madaniyat", r"farg'ona", r"fergana", r"uzreport", r"o'zbekiston", 
    r"ozbekiston", r"ruxsor", r"xorazm", r"andijon", r"qashqadaryo", r"surxondaryo"
]

# 4. РЕГИОНЫ РФ (Города, области, местные ГТРК)
REGIONAL_PATTERNS = [
    r"гтрк", r"дон-тр", r"дон 24", r"губерния", r"бст", r"тнв", r"югра", r"ямал",
    r"кубань", r"башкортостан", r"татарстан", r"моя удмуртия", r"чаваш ен",
    r"самара", r"уфа", r"казань", r"тюмень", r"екатеринбург", r"краснодар", 
    r"красноярск", r"новосибирск", r"владивосток", r"хабаровск", r"крым", 
    r"сочи", r"питер", r"спб", r"нижний новгород", r"челябинск", r"пермь", 
    r"волгоград", r"саратов", r"иркутск", r"воронеж", r"омск", r"ростов", 
    r"барнаул", r"кемерово", r"томск", r"астрахань", r"пенза", r"липецк", 
    r"рязань", r"тула", r"курск", r"тверь", r"ставрополь", r"белгород", 
    r"архангельск", r"вологда", r"калуга", r"чита", r"смоленск", r"курган", 
    r"орел", r"тамбов", r"кострома", r"псков", r"мурманск", r"якутск", 
    r"норильск", r"грозный", r"дагестан", r"осетия", r"армения", r"беларусь"
]

# Объединяем весь черный список
ALL_STOP_PATTERNS = GARBAGE_PATTERNS + ADULT_PATTERNS + UZBEK_PATTERNS + REGIONAL_PATTERNS

# Категории (без 18+)
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
    ]
}

def is_garbage(text):
    text_low = text.lower()
    for pattern in ALL_STOP_PATTERNS:
        if re.search(pattern, text_low):
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
    print("Качаю плейлист...")
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            content = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return

    lines = content.splitlines()
    print(f"Скачано строк: {len(lines)}. Фильтрую мусор, 18+ и узбекские каналы...")

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

            # Проверка дублей ссылок
            if url in seen_urls:
                skipped_duplicates += 1
                current_extinf = None
                continue

            channel_name = current_extinf.split(",")[-1].strip()

            # Проверяем на мусор И название канала, И всю строку #EXTINF целиком (где теги групп)
            full_meta = f"{current_extinf} {channel_name}"
            if is_garbage(full_meta):
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

    print("\nГотово!")
    print(f"-> Удал
