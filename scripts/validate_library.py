#!/usr/bin/env python3
import json
import re
from collections import Counter
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
LIBRARY = SKILL_DIR / "references" / "quote-library.json"
EXPECTED = {"hope", "courage", "persistence", "growth", "action", "change", "future", "journey", "calm-resilience", "city-distance"}


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*", text))


def main() -> None:
    data = json.loads(LIBRARY.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    maximum = data.get("max_entries")
    errors = []
    if maximum != 100:
        errors.append("max_entries must remain 100")
    if len(entries) > 100:
        errors.append(f"library has {len(entries)} entries; hard limit is 100")
    ids = [e.get("id", "") for e in entries]
    texts = [e.get("text", "") for e in entries]
    if len(ids) != len(set(ids)):
        errors.append("duplicate IDs found")
    if len(texts) != len(set(t.casefold() for t in texts)):
        errors.append("duplicate phrase text found")
    for index, entry in enumerate(entries, 1):
        missing = {"id", "category", "text"} - set(entry)
        extra = set(entry) - {"id", "category", "text"}
        if missing:
            errors.append(f"entry {index} missing fields: {sorted(missing)}")
        if extra:
            errors.append(f"entry {index} has forbidden fields: {sorted(extra)}")
        category = entry.get("category")
        text = entry.get("text", "")
        if category not in EXPECTED:
            errors.append(f"entry {index} has unknown category: {category}")
        if text != text.strip() or text.startswith(('"', '“')) or text.endswith(('"', '”')):
            errors.append(f"entry {index} has whitespace or surrounding quotes")
        count = word_count(text)
        if not 4 <= count <= 9:
            errors.append(f"entry {index} has {count} words, expected 4-9: {text}")
        if re.search(r"[{}\[\]]", text):
            errors.append(f"entry {index} contains placeholder punctuation: {text}")
    counts = Counter(e.get("category") for e in entries)
    missing_categories = EXPECTED - set(counts)
    if missing_categories:
        errors.append(f"missing categories: {sorted(missing_categories)}")
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"VALID entries={len(entries)} max={maximum} categories={len(counts)}")
    for category in sorted(counts):
        print(f"{category}={counts[category]}")


if __name__ == "__main__":
    main()
