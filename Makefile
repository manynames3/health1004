.PHONY: test backend frontend ingest

test:
	cd backend && PYTHONPATH=. pytest

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

ingest:
	python scripts/ingest.py --pdf-dir ./pdfs --s3-prefix raw-pdfs/

eval:
	python scripts/evaluate_retrieval.py --top-k 5
