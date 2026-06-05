# Korean OCR Troubleshooting

The ingestion CLI uses embedded text when possible. OCR is only a fallback for scanned or garbled PDFs.

## Tesseract

Install Korean and English language data:

```bash
brew install tesseract tesseract-lang
```

Verify:

```bash
tesseract --list-langs | grep -E "kor|eng"
```

If `kor` is missing, reinstall language packs or set `TESSDATA_PREFIX`.

## PaddleOCR

PaddleOCR often performs better on Korean scanned newsletters, but it is large and can take longer to install:

```bash
pip install paddleocr
```

The script tries:

```python
PaddleOCR(use_angle_cls=True, lang="korean")
```

If PaddleOCR fails, ingestion logs the error and falls back to Tesseract.

## Low-Confidence Files

`ingestion_report.json` includes per-file `extraction_diagnostics` and `empty_or_low_confidence_files`. Review these manually before trusting search quality. Common fields:

- `embedded.total_chars`
- `embedded.avg_chars_per_page`
- `embedded.low_text_pages`
- `embedded.garbled_score`
- `embedded.flags`
- `ocr.engine`
- `ocr.mean_confidence`
- `selected.flags`

Common causes:

- Very low-resolution scans.
- Rotated or skewed pages.
- Mixed handwriting and print.
- PDFs that render page images incorrectly.

For difficult PDFs, manually rescan or preprocess pages at 300 DPI before re-running with `--force`.
