#!/usr/bin/env python3
import argparse
import hashlib
import json
import random
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
LIBRARY = SKILL_DIR / "references" / "quote-library.json"
FALLBACK = ["journey", "future", "hope", "calm-resilience"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Select local postcard phrases without network access.")
    parser.add_argument("--style", default="auto")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--seed", default="default")
    parser.add_argument("--exclude", action="append", default=[], help="Phrase text or stable ID to exclude.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    args = parser.parse_args()

    data = json.loads(LIBRARY.read_text(encoding="utf-8"))
    entries = data["entries"]
    if len(entries) > int(data.get("max_entries", 100)) or len(entries) > 100:
        raise SystemExit("Quote library exceeds the hard 100-entry limit.")
    if args.count < 1:
        raise SystemExit("--count must be positive.")

    excluded = set(args.exclude)
    available = [e for e in entries if e["id"] not in excluded and e["text"] not in excluded]
    categories = sorted({e["category"] for e in available})
    if args.style != "auto" and args.style not in categories:
        raise SystemExit(f"Unknown style: {args.style}. Available: {', '.join(categories)}")

    digest = hashlib.sha256(args.seed.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    chosen = []
    order = categories if args.style == "auto" else [args.style] + [x for x in FALLBACK if x != args.style]
    pools = {category: [e for e in available if e["category"] == category] for category in categories}
    for pool in pools.values():
        rng.shuffle(pool)

    if args.style == "auto":
        while len(chosen) < args.count:
            made_progress = False
            for category in order:
                pool = pools.get(category, [])
                if pool and len(chosen) < args.count:
                    chosen.append(pool.pop())
                    made_progress = True
            if not made_progress:
                break
    else:
        for category in order:
            pool = pools.get(category, [])
            while pool and len(chosen) < args.count:
                chosen.append(pool.pop())

    if len(chosen) < args.count:
        remaining = [e for pool in pools.values() for e in pool]
        rng.shuffle(remaining)
        chosen.extend(remaining[: args.count - len(chosen)])

    if len(chosen) != args.count:
        raise SystemExit(f"Only {len(chosen)} unused phrases available for requested count {args.count}.")
    if args.json:
        print(json.dumps(chosen, ensure_ascii=False, indent=2))
    else:
        for entry in chosen:
            print(entry["text"])


if __name__ == "__main__":
    main()
