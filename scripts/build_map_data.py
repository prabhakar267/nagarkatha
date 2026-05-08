"""
Build cities_for_map.json from indian_books_with_cities.jsonl.
Groups books by city and enriches with covers/by_statement from the dump if available.
"""

import json
from collections import defaultdict
from pathlib import Path

JSONL = Path(__file__).parent.parent / "data" / "indian_books_with_cities.jsonl"
DUMP = Path(__file__).parent.parent / "dumps" / "ol_dump_editions_latest.txt"
OUTPUT = Path(__file__).parent.parent / "data" / "cities_for_map.json"

BOOK_FIELDS = [
    "title", "languages", "publish_date", "key",
    "subjects", "publishers", "authors", "by_statement",
    "description", "number_of_pages", "isbn_13", "isbn_10", "covers",
]


def load_books():
    books = []
    with open(JSONL) as f:
        for line in f:
            books.append(json.loads(line))
    return books


def enrich_from_dump(books):
    """Scan dump to fill in covers and by_statement for books missing them."""
    keys_needing_enrichment = {}
    for i, book in enumerate(books):
        needs_covers = not book.get("covers")
        needs_author = not book.get("by_statement")
        if needs_covers or needs_author:
            keys_needing_enrichment[book["key"]] = (i, needs_covers, needs_author)

    if not keys_needing_enrichment:
        print("All books already enriched, skipping dump scan.")
        return books

    if not DUMP.exists():
        print(f"Dump file not found at {DUMP}, skipping enrichment.")
        return books

    print(f"Scanning dump to enrich {len(keys_needing_enrichment)} books...")
    found = 0
    with open(DUMP) as f:
        for line in f:
            if found >= len(keys_needing_enrichment):
                break
            parts = line.split('\t', 5)
            if len(parts) < 5:
                continue
            try:
                data = json.loads(parts[4])
            except (json.JSONDecodeError, IndexError):
                continue
            key = data.get("key")
            if key in keys_needing_enrichment:
                idx, needs_covers, needs_author = keys_needing_enrichment[key]
                if needs_covers and data.get("covers"):
                    books[idx]["covers"] = data["covers"]
                if needs_author and data.get("by_statement"):
                    books[idx]["by_statement"] = data["by_statement"]
                found += 1

    print(f"  Enriched {found} books from dump.")
    return books


def group_by_city(books):
    cities = defaultdict(lambda: {"books": []})
    for book in books:
        for cp in book.get("city_places", []):
            city_key = (cp["city_name"], cp["latitude"], cp["longitude"])
            city = cities[city_key]
            city["city_name"] = cp["city_name"]
            city["latitude"] = cp["latitude"]
            city["longitude"] = cp["longitude"]
            city["population"] = cp["population"]
            city["country_code"] = cp["country_code"]

            book_record = {}
            for field in BOOK_FIELDS:
                val = book.get(field)
                if val is not None and val != [] and val != "":
                    book_record[field] = val
            city["books"].append(book_record)

    return list(cities.values())


def deduplicate_books(cities):
    for city in cities:
        seen_keys = set()
        unique = []
        for book in city["books"]:
            key = book.get("key")
            if key and key in seen_keys:
                continue
            if key:
                seen_keys.add(key)
            unique.append(book)
        city["books"] = unique
    return cities


def main():
    print("Loading books...")
    books = load_books()
    print(f"  {len(books)} books loaded.")

    books = enrich_from_dump(books)

    print("Grouping by city...")
    cities = group_by_city(books)
    cities = deduplicate_books(cities)
    cities.sort(key=lambda c: len(c["books"]), reverse=True)

    print(f"  {len(cities)} cities, {sum(len(c['books']) for c in cities)} book entries.")

    with open(OUTPUT, "w") as f:
        json.dump(cities, f, ensure_ascii=False)

    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
