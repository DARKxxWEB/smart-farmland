import re
import unicodedata

from utils.thresholds import THRESHOLDS

_DOCUMENTS = (
    {
        "id": "dashboard-guide",
        "title": "راهنمای پایش هوشمند مزرعه",
        "keywords": "داشبورد پنل حسگر داده ثبت شده پایش زمان آخرین دریافت روند نمودار",
        "content": (
            "داشبورد هوشمند مزرعه خلاصه داده‌های دریافت‌شده از حسگرها را نمایش می‌دهد. "
            "زمان آخرین دریافت، زمان ثبت داده در حسگر است و الزاماً به معنی برخط‌بودن "
            "دستگاه در همین لحظه نیست. نمودارها از میانگین اندازه‌گیری‌های ثبت‌شده در "
            "بازه‌های زمانی ساعتی یا روزانه ساخته می‌شوند."
        ),
    },
    {
        "id": "metric-guide",
        "title": "راهنمای شاخص‌های اندازه‌گیری",
        "keywords": "رطوبت moisture_pct دما temperature_c نیتروژن nitrogen_mgkg فسفر phosphorus_mgkg پتاسیم potassium_mgkg واحد",
        "content": (
            "moisture_pct رطوبت گزارش‌شده برحسب درصد است. temperature_c دما برحسب "
            "درجه سلسیوس است. nitrogen_mgkg، phosphorus_mgkg و potassium_mgkg "
            "به‌ترتیب نیتروژن، فسفر و پتاسیم گزارش‌شده برحسب میلی‌گرم بر کیلوگرم هستند. "
            "تفسیر مقدار به نوع حسگر، محل نمونه‌برداری، خاک و محصول وابسته است."
        ),
    },
    {
        "id": "alert-policy",
        "title": "راهنمای هشدارها و آستانه‌های سامانه",
        "keywords": "هشدار آستانه حد پایین حد بالا بحرانی ساکت silence threshold",
        "content": (
            "هشدار آستانه هنگامی ساخته می‌شود که اندازه‌گیری از حد پایین یا بالای "
            "تنظیم‌شده برای آن شاخص عبور کند. حسگر در صورت نداشتن گزارش تازه‌تر از "
            "بازه سکوت تنظیم‌شده، هشدار سکوت می‌گیرد. سطح هشدار حاصل قواعد قطعی سامانه "
            "است؛ این آستانه‌ها عمومی‌اند و نسخه پزشکی/کشاورزی یا توصیه اختصاصی یک "
            "محصول یا مزرعه محسوب نمی‌شوند."
        ),
    },
    {
        "id": "advice-safety",
        "title": "حدود توصیه‌های دستیار",
        "keywords": "توصیه کود سم آبیاری درمان نسخه محصول کشاورزی عدم قطعیت ایمنی",
        "content": (
            "دستیار فقط می‌تواند داده‌های ثبت‌شده، روندها، هشدارها و راهنمای این سامانه "
            "را توضیح دهد. برای تعیین مقدار یا زمان مصرف کود، سم، آبیاری یا نسخه متناسب "
            "با محصول، خاک و اقلیم، اطلاعات تخصصی مزرعه و نظر کارشناس کشاورزی لازم است؛ "
            "نباید از روی یک هشدار عمومی نسخه قطعی ارائه شود."
        ),
    },
)

_STOP_WORDS = {
    "از", "با", "برای", "به", "در", "را", "که", "این", "آن", "چه", "چرا",
    "چطور", "چگونه", "هست", "است", "می", "شود", "شده", "یک", "و", "یا",
    "the", "is", "a", "an", "of", "to", "for", "in", "on", "and", "what",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(
        str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"})
    )
    return "".join(char for char in text if unicodedata.category(char) != "Mn").lower()


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[\w%.-]+", _normalize(text))
        if len(token) > 1 and token not in _STOP_WORDS
    ]


def search_knowledge(query: str, limit: int = 3) -> list[dict[str, str]]:
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return []

    documents = [
        *_DOCUMENTS,
        {
            "id": "live-thresholds",
            "title": "آستانه‌های فعال تنظیم‌شده در BI",
            "keywords": "آستانه حد پایین حد بالا رطوبت دما نیتروژن فسفر پتاسیم",
            "content": "آستانه‌های فعال فعلی سامانه (مقدار هر شاخص با واحد همان حسگر): "
            + "؛ ".join(
                f"{metric}: حد پایین {limits['low']} و حد بالا {limits['high']} {limits['unit']}"
                for metric, limits in THRESHOLDS.items()
            ),
        },
    ]

    ranked = []
    for document in documents:
        document_tokens = _tokens(f"{document['title']} {document['keywords']} {document['content']}")
        overlap = query_tokens.intersection(document_tokens)
        score = len(overlap)
        if score:
            ranked.append((score, document))

    ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [
        {
            "id": document["id"],
            "title": document["title"],
            "content": document["content"],
        }
        for _, document in ranked[: max(1, min(limit, 5))]
    ]
