"""
Filter indian_books_with_places.jsonl to only books with city-level places.
Enriches each place with geonamescache metadata (lat, lon, population, country).
Output: indian_books_with_cities.jsonl
"""

import json
import geonamescache
from pathlib import Path

INPUT = Path(__file__).parent / "data" / "indian_books_with_places.jsonl"
OUTPUT = Path(__file__).parent / "data" / "indian_books_with_cities.jsonl"

gc = geonamescache.GeonamesCache()

# Build lookup: city name -> city info (pick largest by population if duplicates)
city_lookup = {}
for c in gc.get_cities().values():
    name = c["name"]
    if name not in city_lookup or c["population"] > city_lookup[name]["population"]:
        city_lookup[name] = c

# Also build a "cleaned name" lookup for entries like "Delhi (India)"
# Strip parenthetical suffixes and try matching
def resolve_city(place):
    """Try to match a place string to a city. Returns city info dict or None."""
    if place in city_lookup:
        return city_lookup[place]
    clean = place.split("(")[0].strip()
    if clean in city_lookup:
        return city_lookup[clean]
    return None

count = 0
with open(INPUT) as fin, open(OUTPUT, "w") as fout:
    for line in fin:
        book = json.loads(line)
        city_places = []
        for p in book.get("subject_places", []):
            city = resolve_city(p)
            if city:
                city_places.append({
                    "original_value": p,
                    "city_name": city["name"],
                    "latitude": city["latitude"],
                    "longitude": city["longitude"],
                    "population": city["population"],
                    "country_code": city["countrycode"],
                    "timezone": city["timezone"],
                })
        if city_places:
            book["city_places"] = city_places
            # Keep only city entries in subject_places
            book["subject_places"] = [cp["original_value"] for cp in city_places]
            fout.write(json.dumps(book, ensure_ascii=False) + "\n")
            count += 1

print(f"✓ {count} books with city-level places saved to {OUTPUT}")
