.PHONY: test backend frontend ingest taxonomy tag reindex eval-taxonomy

test:
	cd backend && PYTHONPATH=. pytest

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

ingest:
	python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/

taxonomy:
	python scripts/build_taxonomy.py --seed data/taxonomy.seed.yaml

tag:
	python scripts/tag_passages.py --source existing --report outputs/taxonomy_report.json

reindex:
	python scripts/reindex_with_taxonomy.py --rebuild

eval:
	python scripts/evaluate_retrieval.py --top-k 5

eval-taxonomy:
	python scripts/evaluate_taxonomy_retrieval.py
