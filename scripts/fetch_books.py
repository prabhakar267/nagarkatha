"""
Fetch all books in Indian languages from Open Library API.
Saves results as JSONL (one JSON object per book) per language.
Supports resume on failure — re-run and it picks up where it left off.
"""

import json
import os
import ssl
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# macOS Python often lacks default certs
SSL_CTX = ssl.create_default_context()
try:
    import certifi
    SSL_CTX.load_verify_locations(certifi.where())
except ImportError:
    SSL_CTX.check_hostname = False
    SSL_CTX.verify_mode = ssl.CERT_NONE

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

INDIAN_LANGUAGES = {
    "hin": "Hindi",
    "tam": "Tamil",
    "tel": "Telugu",
    "ben": "Bengali",
    "mar": "Marathi",
    "guj": "Gujarati",
    "kan": "Kannada",
    "mal": "Malayalam",
    "pan": "Punjabi",
    "urd": "Urdu",
    "ori": "Odia",
    "san": "Sanskrit",
    "asm": "Assamese",
    "kas": "Kashmiri",
    "sin": "Sindhi",
    "nep": "Nepali",
    "kon": "Konkani",
    "mai": "Maithili",
    "sat": "Santali",
    "doi": "Dogri",
    "mni": "Manipuri",
    "bod": "Bodo",
}

FIELDS = [
    "key", "title", "author_name", "author_key",
    "first_publish_year", "publish_year", "publish_date",
    "publisher", "publish_place", "language", "subject", "place",
    "number_of_pages_median", "edition_count", "isbn", "first_sentence",
    "cover_i", "ebook_access", "has_fulltext",
    "ratings_average", "ratings_count", "readinglog_count",
    "want_to_read_count", "already_read_count", "currently_reading_count",
    "lcc", "ddc", "format", "id_amazon",
]

BATCH_SIZE = 100
RATE_LIMIT_DELAY = 1.0
MAX_RETRIES = 5
PROGRESS_FILE = OUTPUT_DIR / "_progress.json"


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)


def fetch_page(lang_code, offset):
    params = urllib.parse.urlencode({
        "q": f"language:{lang_code}",
        "limit": BATCH_SIZE,
        "offset": offset,
        "fields": ",".join(FIELDS),
    })
    url = f"https://openlibrary.org/search.json?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "IndianBooksResearch/1.0 (prabhakar.gupta@nsitonline.in)"})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
        return json.loads(resp.read())


def fetch_language(lang_code, lang_name, progress):
    outfile = OUTPUT_DIR / f"{lang_code}_{lang_name.lower()}.jsonl"

    # Resume: use progress file to determine offset
    offset = progress.get(lang_code, {}).get("offset", 0)
    total = progress.get(lang_code, {}).get("total", None)

    if offset > 0 and total and offset >= total:
        print(f"  ✓ {lang_name}: already complete ({total} books)")
        return offset

    if offset > 0:
        print(f"  ↻ Resuming {lang_name} from offset {offset}/{total or '?'}")

    with open(outfile, "a") as f:
        while True:
            retries = 0
            data = None
            while retries < MAX_RETRIES:
                try:
                    data = fetch_page(lang_code, offset)
                    break
                except Exception as e:
                    retries += 1
                    wait = retries * 5
                    print(f"\n  ⚠ Error at offset {offset}: {e}. Retry {retries}/{MAX_RETRIES} in {wait}s...")
                    time.sleep(wait)

            if data is None:
                print(f"\n  ✗ {lang_name}: failed after {MAX_RETRIES} retries at offset {offset}. Run again to resume.")
                return offset

            if total is None:
                total = data["numFound"]
                print(f"  {lang_name} ({lang_code}): {total:,} books total")

            docs = data.get("docs", [])
            if not docs:
                break

            for doc in docs:
                doc["_language_query"] = lang_code
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

            offset += len(docs)

            # Save progress after each batch
            progress[lang_code] = {"offset": offset, "total": total}
            save_progress(progress)

            # Progress
            pct = (offset / total * 100) if total else 0
            if sys.stdout.isatty():
                bar_len = 30
                filled = int(bar_len * offset / total) if total else 0
                bar = "█" * filled + "░" * (bar_len - filled)
                sys.stdout.write(f"\r    [{bar}] {offset:,}/{total:,} ({pct:.1f}%)")
                sys.stdout.flush()
            else:
                # Log-friendly: print every 1000 records
                if offset % 1000 == 0 or offset >= total:
                    print(f"    {offset:,}/{total:,} ({pct:.1f}%)", flush=True)

            if offset >= total:
                break

            time.sleep(RATE_LIMIT_DELAY)

    print(f"\n  ✓ {lang_name}: {offset:,} books saved to {outfile.name}")
    progress[lang_code] = {"offset": offset, "total": total, "done": True}
    save_progress(progress)
    return offset


def main():
    print("=" * 60)
    print("Open Library — Indian Languages Book Fetcher")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Languages: {len(INDIAN_LANGUAGES)}")
    print("=" * 60)

    progress = load_progress()
    grand_total = 0
    start_time = time.time()

    for i, (code, name) in enumerate(INDIAN_LANGUAGES.items(), 1):
        print(f"\n[{i}/{len(INDIAN_LANGUAGES)}] {name} ({code})")
        count = fetch_language(code, name, progress)
        grand_total += count

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Done. Total books: {grand_total:,} | Time: {elapsed/60:.1f} min")
    print(f"Data: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
