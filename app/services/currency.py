"""
Сервис для получения курсов валют.
Использует бесплатный API exchangerate-api.
"""

import aiohttp
from app.utils.logger import logger

# Валюты привязанные к языкам
LANG_CURRENCIES = {
    "ru": "RUB",
    "en": "USD",
    "tg": "TJS",
    "uz": "UZS",
}

CURRENCY_NAMES = {
    "ru": {"USD": "Доллар США", "EUR": "Евро", "RUB": "Российский рубль", "TJS": "Таджикский сомони", "UZS": "Узбекский сум", "KGS": "Кыргызский сом", "KZT": "Казахский тенге", "CNY": "Китайский юань", "GBP": "Фунт стерлингов", "TRY": "Турецкая лира"},
    "en": {"USD": "US Dollar", "EUR": "Euro", "RUB": "Russian Ruble", "TJS": "Tajik Somoni", "UZS": "Uzbek Som", "KGS": "Kyrgyz Som", "KZT": "Kazakh Tenge", "CNY": "Chinese Yuan", "GBP": "British Pound", "TRY": "Turkish Lira"},
    "tg": {"USD": "Доллари ИМА", "EUR": "Евро", "RUB": "Рубли русӣ", "TJS": "Сомонии тоҷикӣ", "UZS": "Сӯми ӯзбекӣ", "KGS": "Соми қирғизӣ", "KZT": "Тенгеи қазоқӣ", "CNY": "Юани хитоӣ", "GBP": "Фунти стерлинг", "TRY": "Лираи туркӣ"},
    "uz": {"USD": "AQSh dollari", "EUR": "Yevro", "RUB": "Rus rubli", "TJS": "Tojik somoniy", "UZS": "O'zbek so'mi", "KGS": "Qirg'iz somi", "KZT": "Qozoq tengesi", "CNY": "Xitoy yuani", "GBP": "Britaniya funti", "TRY": "Turk lirasi"},
}

# Какие валюты показывать
DISPLAY_CURRENCIES = ["USD", "EUR", "RUB", "TJS", "UZS", "KZT", "TRY", "CNY"]


async def get_exchange_rates(base: str = "USD") -> dict:
    """
    Получает курсы валют относительно base.
    Возвращает dict {currency_code: rate} или пустой dict при ошибке.
    """
    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("result") == "success":
                        return data.get("rates", {})
        logger.error(f"Exchange rate API returned non-200: {url}")
    except Exception as e:
        logger.error(f"Exchange rate fetch error: {e}")
    return {}


def format_currency_message(rates: dict, base: str, lang: str) -> str:
    """Форматирует сообщение с курсами валют в понятном виде."""
    names = CURRENCY_NAMES.get(lang, CURRENCY_NAMES["ru"])
    flags = {"USD": "🇺🇸", "EUR": "🇪🇺", "RUB": "🇷🇺", "TJS": "🇹🇯", "UZS": "🇺🇿", "KZT": "🇰🇿", "TRY": "🇹🇷", "CNY": "🇨🇳", "GBP": "🇬🇧", "KGS": "🇰🇬"}
    base_flag = flags.get(base, "")
    base_name = names.get(base, base)

    header = {
        "ru": f"💱 <b>Курсы валют</b>\n\n{base_flag} Твоя валюта: <b>{base_name} ({base})</b>\n\n",
        "en": f"💱 <b>Exchange Rates</b>\n\n{base_flag} Your currency: <b>{base_name} ({base})</b>\n\n",
        "tg": f"💱 <b>Курби асъор</b>\n\n{base_flag} Асъори шумо: <b>{base_name} ({base})</b>\n\n",
        "uz": f"💱 <b>Valyuta kurslari</b>\n\n{base_flag} Sizning valyutangiz: <b>{base_name} ({base})</b>\n\n",
    }

    buy_label = {"ru": "Покупка", "en": "Buy", "tg": "Хариданӣ", "uz": "Sotib olish"}.get(lang, "Buy")

    lines = []
    for cur in DISPLAY_CURRENCIES:
        if cur == base or cur not in rates:
            continue
        rate = rates[cur]
        name = names.get(cur, cur)
        flag = flags.get(cur, "")

        # Сколько base нужно за 1 единицу cur
        if rate > 0:
            inverse = 1 / rate
        else:
            continue

        # Форматируем понятно: "1 USD = 87.50 RUB" и "1 RUB = 0.0114 USD"
        if rate >= 100:
            rate_str = f"{rate:,.2f}".replace(",", " ")
        elif rate >= 1:
            rate_str = f"{rate:.2f}"
        else:
            rate_str = f"{rate:.4f}"

        if inverse >= 100:
            inv_str = f"{inverse:,.2f}".replace(",", " ")
        elif inverse >= 1:
            inv_str = f"{inverse:.2f}"
        else:
            inv_str = f"{inverse:.4f}"

        lines.append(
            f"{flag} <b>{name}</b>\n"
            f"    1 {base} = <b>{rate_str}</b> {cur}\n"
            f"    1 {cur} = <b>{inv_str}</b> {base}\n"
        )

    from datetime import datetime
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    footer = {
        "ru": f"\n🕐 Обновлено: {now}",
        "en": f"\n🕐 Updated: {now}",
        "tg": f"\n🕐 Навсозӣ: {now}",
        "uz": f"\n🕐 Yangilangan: {now}",
    }

    return header.get(lang, header["ru"]) + "\n".join(lines) + footer.get(lang, footer["ru"])
