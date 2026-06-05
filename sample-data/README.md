# Sample Data

Do not commit the 572 private PDFs to this repository.

For local smoke tests, place one or two non-sensitive PDFs in `../pdfs` and run:

```bash
python scripts/ingest.py --pdf-dir ./pdfs --limit 2
```

The ingestion report will be written to S3 at:

```text
ingestion-reports/ingestion_report.json
```
