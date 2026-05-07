"""
Add native script titles to cities_for_map.json using indic-transliteration.
Best-effort: transliterates IAST-like romanized titles to native script.
Falls back to None if language not supported.
"""

import json
from pathlib import Path
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

DATA = Path(__file__).parent.parent / "data" / "cities_for_map.json"

LANG_TO_SCRIPT = {
    '/languages/hin': sanscript.DEVANAGARI,
    '/languages/san': sanscript.DEVANAGARI,
    '/languages/mar': sanscript.DEVANAGARI,
    '/languages/nep': sanscript.DEVANAGARI,
    '/languages/mai': sanscript.DEVANAGARI,
    '/languages/doi': sanscript.DEVANAGARI,
    '/languages/kon': sanscript.DEVANAGARI,
    '/languages/ben': sanscript.BENGALI,
    '/languages/asm': sanscript.BENGALI,
    '/languages/tam': sanscript.TAMIL,
    '/languages/tel': sanscript.TELUGU,
    '/languages/kan': sanscript.KANNADA,
    '/languages/mal': sanscript.MALAYALAM,
    '/languages/guj': sanscript.GUJARATI,
    '/languages/pan': sanscript.GURMUKHI,
    '/languages/ori': sanscript.ORIYA,
}

def is_already_native(title):
    """Check if title already contains non-Latin characters."""
    return any(ord(c) > 0x024F for c in title)

def transliterate_title(title, lang):
    if is_already_native(title):
        return title
    script = LANG_TO_SCRIPT.get(lang)
    if not script:
        return None
    try:
        return transliterate(title, sanscript.IAST, script)
    except:
        return None

with open(DATA) as f:
    cities = json.load(f)

total = 0
converted = 0
for city in cities:
    for book in city["books"]:
        total += 1
        lang = book["languages"][0] if book["languages"] else None
        native = transliterate_title(book["title"], lang)
        book["title_native"] = native
        if native and native != book["title"]:
            converted += 1

with open(DATA, "w") as f:
    json.dump(cities, f, ensure_ascii=False)

print(f"Total books: {total}")
print(f"Transliterated: {converted}")
print(f"Skipped (unsupported lang or already native): {total - converted}")
