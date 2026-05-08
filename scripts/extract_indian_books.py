"""
Extract all Indian-language books with place data from the Open Library editions dump.
Uses DuckDB to query the gzipped TSV directly — no decompression needed.
Output: indian_books_with_places.jsonl
"""

import duckdb
import json
from pathlib import Path

DUMP = Path(__file__).parent / "dumps" / "ol_dump_editions_latest.txt.gz"
OUTPUT = Path(__file__).parent / "data" / "indian_books_with_places.jsonl"
OUTPUT.parent.mkdir(exist_ok=True)

INDIAN_LANGS = [
    '/languages/hin', '/languages/tam', '/languages/tel', '/languages/ben',
    '/languages/mar', '/languages/guj', '/languages/kan', '/languages/mal',
    '/languages/pan', '/languages/urd', '/languages/ori', '/languages/san',
    '/languages/asm', '/languages/kas', '/languages/snd', '/languages/nep',
    '/languages/kon', '/languages/mai', '/languages/sat', '/languages/doi',
    '/languages/mni', '/languages/bod',
]

lang_list = ", ".join(f"'{l}'" for l in INDIAN_LANGS)

query = f"""
SELECT column4 as json_data
FROM read_csv('{DUMP}', sep='\t', header=false, max_line_size=20000000,
     columns={{'column0': 'VARCHAR', 'column1': 'VARCHAR', 'column2': 'VARCHAR', 'column3': 'VARCHAR', 'column4': 'VARCHAR'}},
     quote='', ignore_errors=true)
WHERE column0 = '/type/edition'
  AND column4 LIKE '%subject_places%'
  AND (column4 LIKE '%/languages/hin%' OR column4 LIKE '%/languages/tam%' OR column4 LIKE '%/languages/tel%'
    OR column4 LIKE '%/languages/ben%' OR column4 LIKE '%/languages/mar%' OR column4 LIKE '%/languages/guj%'
    OR column4 LIKE '%/languages/kan%' OR column4 LIKE '%/languages/mal%' OR column4 LIKE '%/languages/pan%'
    OR column4 LIKE '%/languages/urd%' OR column4 LIKE '%/languages/ori%' OR column4 LIKE '%/languages/san%'
    OR column4 LIKE '%/languages/asm%' OR column4 LIKE '%/languages/kas%' OR column4 LIKE '%/languages/snd%'
    OR column4 LIKE '%/languages/nep%' OR column4 LIKE '%/languages/kon%' OR column4 LIKE '%/languages/mai%'
    OR column4 LIKE '%/languages/sat%' OR column4 LIKE '%/languages/doi%' OR column4 LIKE '%/languages/mni%'
    OR column4 LIKE '%/languages/bod%')
"""

print("Querying dump (this will take 10-20 minutes)...")
print(f"Input: {DUMP}")
print(f"Output: {OUTPUT}")

con = duckdb.connect()
result = con.execute(query).fetchall()

print(f"Found {len(result)} editions")

count = 0
with open(OUTPUT, 'w') as f:
    for row in result:
        try:
            data = json.loads(row[0])
        except:
            continue
        places = data.get("subject_places", [])
        if not places:
            continue
        record = {
            "key": data.get("key"),
            "title": data.get("title"),
            "authors": [a.get("key") for a in data.get("authors", []) if isinstance(a, dict)],
            "by_statement": data.get("by_statement"),
            "languages": [l.get("key") for l in data.get("languages", []) if isinstance(l, dict)],
            "subject_places": places,
            "subjects": data.get("subjects", []),
            "publish_date": data.get("publish_date"),
            "publishers": data.get("publishers", []),
            "number_of_pages": data.get("number_of_pages"),
            "isbn_13": data.get("isbn_13", []),
            "isbn_10": data.get("isbn_10", []),
            "covers": data.get("covers", []),
            "description": data.get("description", {}).get("value") if isinstance(data.get("description"), dict) else data.get("description"),
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        count += 1

print(f"✓ Saved {count} books to {OUTPUT}")
