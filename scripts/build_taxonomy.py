#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings
from app.taxonomy import load_taxonomy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the controlled Health1004 Korean taxonomy artifact.")
    parser.add_argument("--seed", default="data/taxonomy.seed.yaml", help="Path to taxonomy.seed.yaml")
    parser.add_argument("--out", default="outputs/taxonomy.json", help="Local JSON artifact path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    taxonomy = load_taxonomy(args.seed)
    payload = taxonomy.to_public_dict()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote taxonomy artifact: {out_path}")
    print(f"topics={payload['topic_count']} aliases={payload['alias_count']}")

    if settings.database_url:
        try:
            from app.db import make_session_factory
            from app.taxonomy_store import upsert_taxonomy

            with make_session_factory(settings)() as session:
                counts = upsert_taxonomy(session, taxonomy)
            print(f"Upserted taxonomy to database: {counts}")
        except Exception as exc:
            print(f"Database taxonomy upsert skipped/failed: {exc}")
    else:
        print("DATABASE_URL is not set; wrote local taxonomy artifact only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
