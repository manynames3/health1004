#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_PDF_DIR="/Users/aidenrhaa/Documents/Codex/2026-06-04/i-need-to-find-all-emails/work/hschung-pdfs/3탄"
PDF_DIR="$DEFAULT_PDF_DIR"
S3_PREFIX="raw-pdfs/"
PYTHON_BIN="${PYTHON_BIN:-}"
FORCE=0
SMOKE=0
SKIP_TAXONOMY=0
RUN_EVALUATION=0

usage() {
  cat <<'USAGE'
One-time Health1004 upload/ingestion script for the 3탄 PDF folder.

Usage:
  scripts/upload_3tan_once.sh [options]

Options:
  --smoke            Ingest only 3 PDFs to a smoke-test vector key.
  --force            Reprocess PDFs even if checksums match.
  --skip-taxonomy    Only upload/ingest PDFs; skip taxonomy tagging/reindex plan.
  --evaluate         Run the 12-question taxonomy retrieval evaluation after full ingest.
  --pdf-dir PATH     Override the source PDF directory.
  --python PATH      Override the Python interpreter.
  -h, --help         Show this help.

Recommended:
  scripts/upload_3tan_once.sh --smoke
  scripts/upload_3tan_once.sh
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke)
      SMOKE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --skip-taxonomy)
      SKIP_TAXONOMY=1
      shift
      ;;
    --evaluate)
      RUN_EVALUATION=1
      shift
      ;;
    --pdf-dir)
      PDF_DIR="${2:?--pdf-dir requires a path}"
      shift 2
      ;;
    --python)
      PYTHON_BIN="${2:?--python requires a path}"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "$ROOT_DIR/../../work/verify-venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/../../work/verify-venv/bin/python"
  elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  else
    PYTHON_BIN="$(command -v python3)"
  fi
fi

cd "$ROOT_DIR"
mkdir -p outputs

TIMESTAMP="$(date +"%Y%m%d-%H%M%S")"
if [[ "$SMOKE" -eq 1 ]]; then
  RUN_LABEL="3tan-smoke-$TIMESTAMP"
  REPORT_PATH="outputs/ingestion_3tan_smoke_$TIMESTAMP.json"
  LOG_PATH="outputs/ingestion_3tan_smoke_$TIMESTAMP.log"
  VECTOR_ARGS=(--limit 3 --vector-bundle-key "vector-index/chunks.smoke.json.gz")
else
  RUN_LABEL="3tan-full-$TIMESTAMP"
  REPORT_PATH="outputs/ingestion_3tan_full_$TIMESTAMP.json"
  LOG_PATH="outputs/ingestion_3tan_full_$TIMESTAMP.log"
  VECTOR_ARGS=()
fi

exec > >(tee -a "$LOG_PATH") 2>&1

echo "== Health1004 one-time ingestion =="
echo "run_label=$RUN_LABEL"
echo "repo=$ROOT_DIR"
echo "pdf_dir=$PDF_DIR"
echo "s3_prefix=$S3_PREFIX"
echo "python=$PYTHON_BIN"
echo "report=$REPORT_PATH"
echo "log=$LOG_PATH"
echo

if [[ ! -d "$PDF_DIR" ]]; then
  echo "PDF directory does not exist: $PDF_DIR" >&2
  exit 1
fi

PDF_COUNT="$(find "$PDF_DIR" -type f -iname '*.pdf' | wc -l | tr -d ' ')"
PDF_SIZE="$(du -sh "$PDF_DIR" | awk '{print $1}')"
echo "source_pdf_count=$PDF_COUNT"
echo "source_pdf_size=$PDF_SIZE"

if [[ "$PDF_COUNT" -eq 0 ]]; then
  echo "No PDFs found in $PDF_DIR" >&2
  exit 1
fi

if command -v aws >/dev/null 2>&1; then
  echo
  echo "== AWS caller =="
  aws sts get-caller-identity --output json
fi

export PYTHONPATH="$ROOT_DIR/backend${PYTHONPATH:+:$PYTHONPATH}"

INGEST_ARGS=(
  scripts/ingest.py
  --pdf-dir "$PDF_DIR"
  --s3-prefix "$S3_PREFIX"
  --report-path "$REPORT_PATH"
  "${VECTOR_ARGS[@]}"
)

if [[ "$FORCE" -eq 1 ]]; then
  INGEST_ARGS+=(--force)
fi

echo
echo "== Ingest PDFs =="
"$PYTHON_BIN" "${INGEST_ARGS[@]}"

if [[ "$SMOKE" -eq 1 ]]; then
  echo
  echo "Smoke ingest complete. The smoke run used vector-index/chunks.smoke.json.gz and did not update taxonomy artifacts."
  echo "Review $REPORT_PATH, then run scripts/upload_3tan_once.sh for the full upload."
  exit 0
fi

if [[ "$SKIP_TAXONOMY" -eq 1 ]]; then
  echo
  echo "PDF ingest complete. Taxonomy/reindex steps skipped by --skip-taxonomy."
  exit 0
fi

echo
echo "== Build taxonomy artifact =="
"$PYTHON_BIN" scripts/build_taxonomy.py --seed data/taxonomy.seed.yaml --out outputs/taxonomy.json

echo
echo "== Tag passages with taxonomy =="
"$PYTHON_BIN" scripts/tag_passages.py --source existing --report outputs/taxonomy_report.json

echo
echo "== Reindex with taxonomy metadata =="
"$PYTHON_BIN" scripts/reindex_with_taxonomy.py --rebuild

if [[ "$RUN_EVALUATION" -eq 1 ]]; then
  echo
  echo "== Evaluate taxonomy retrieval =="
  "$PYTHON_BIN" scripts/evaluate_taxonomy_retrieval.py
else
  echo
  echo "Evaluation skipped. Add --evaluate to run the 12-question retrieval check."
fi

echo
echo "Done."
echo "Ingestion report: $REPORT_PATH"
echo "Log: $LOG_PATH"
