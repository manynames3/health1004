# Architecture

Health1004 is a taxonomy-first Korean PDF archive with an optional assistant layer. The default architecture favors low operating cost: static frontend, private S3 corpus storage, manual ingestion, Bedrock calls only when needed, and an S3-hosted vector bundle instead of an always-on search cluster.

## Container View

```mermaid
flowchart TB
    User["Reader or archive reviewer"]
    Admin["Archive admin"]

    subgraph Edge["Cloudflare"]
        Pages["Cloudflare Pages\nNext.js static export"]
    end

    subgraph App["API runtime\nlocal or Lambda Function URL"]
        FastAPI["FastAPI backend"]
        Resolver["Korean query resolver\naliases and taxonomy filters"]
        Retriever["Hybrid retrieval\nmetadata, keyword, vector"]
        Ingestion["Manual ingestion pipeline"]
    end

    subgraph AWS["AWS account"]
        S3["Private S3 corpus bucket\nPDFs, extracted text, reports,\nvector bundles"]
        Bedrock["Amazon Bedrock Runtime\nTitan embeddings\nHaiku/Nova answers"]
        OpenSearch["Optional existing OpenSearch endpoint\nmetadata filters and Nori analyzer"]
    end

    subgraph Data["Local or hosted database"]
        Postgres["Postgres\nSQLAlchemy and Alembic"]
    end

    User --> Pages
    Pages --> FastAPI
    Admin --> Pages
    Admin --> FastAPI
    FastAPI --> Resolver
    Resolver --> Retriever
    Retriever --> S3
    Retriever -. optional .-> OpenSearch
    FastAPI --> Bedrock
    FastAPI --> Postgres
    Ingestion --> S3
    Ingestion --> Bedrock
    Ingestion --> Postgres
```

## Runtime Query Flow

```mermaid
sequenceDiagram
    participant UI as Next.js UI
    participant API as FastAPI
    participant Tax as Taxonomy resolver
    participant Store as S3 vector bundle or OpenSearch
    participant BR as Bedrock

    UI->>API: POST /query
    API->>Tax: Normalize Korean query and match aliases
    Tax-->>API: Canonical topics, aliases, filters
    API->>Store: Load active vector bundle metadata
    Store-->>API: embedding model and dimension
    API->>BR: Embed query with bundle-matched embedding model
    API->>Store: Search tagged passages first
    Store-->>API: Retrieved chunks with page spans
    API->>Store: Broader hybrid fallback if needed
    API->>BR: Generate answer from retrieved context only
    API-->>UI: Answer, citations, source passages, request_id
```

The answer path is grounded by design. If retrieval returns weak or empty context, the API should not ask the model to invent an answer.

## Bedrock Model Boundary

The default model profile is documented in [model-strategy.md](model-strategy.md):

- primary answer model: `anthropic.claude-haiku-4-5-20251001-v1:0`
- fallback answer model: `amazon.nova-2-lite-v1:0`
- embedding model: `amazon.titan-embed-text-v2:0`
- reranking disabled by default

Answer models can be changed independently of the vector bundle. Embedding model changes require rebuilding vectors because stored passage vectors and query vectors must share the same embedding model and dimension.

## Ingestion Flow

```mermaid
flowchart LR
    PDFs["Local PDFs"] --> Upload["Upload raw PDFs to S3"]
    Upload --> Extract["Extract embedded text with PyMuPDF"]
    Extract --> OCR{"Text quality OK?"}
    OCR -- no --> OCRFallback["Try Korean OCR\nPaddleOCR or Tesseract"]
    OCR -- yes --> Pages["Page JSON and Markdown"]
    OCRFallback --> Pages
    Pages --> Chunk["Korean-aware chunking\npage spans preserved"]
    Chunk --> Embed["Titan Text Embeddings V2"]
    Embed --> Bundle["chunks.json.gz\nS3 vector bundle"]
    Chunk --> Taxonomy["Deterministic alias tagging"]
    Taxonomy --> Report["ingestion_report.json\ntaxonomy_report.json"]
    Taxonomy --> DB["Optional Postgres upsert"]
```

The corpus is manually ingested. There are no crawlers, recurring jobs, or scheduled data pulls.

## Data Model

The structured schema lives in `backend/app/db_models.py` and is migrated by Alembic. It includes:

- `documents`, `articles`, `pages`, `passages`
- `topics`, `topic_aliases`, `body_systems`
- `foods`, `conditions`, `symptoms`, `substances`, `habits`
- `passage_topic_assignments`, `retrieval_logs`

Each passage keeps citation and review metadata such as `document_id`, `article_id`, `page_start`, `page_end`, `section_heading`, `original_korean_text`, category tags, `topic_slugs`, `confidence_score`, `needs_human_review`, source S3 keys, `embedding_id`, and `chunk_id`.

## Source Traceability

Chunks and citations are page-aware. Returned citations include, where available:

- PDF filename
- document title
- detected date
- page start and end
- section heading
- original Korean quote
- document and chunk identifiers
- signed PDF URL

## OpenSearch Boundary

OpenSearch is optional. The default Terraform does not provision it because this is a low-volume archive. `scripts/reindex_with_taxonomy.py` can write local mapping and reindex plans without a live endpoint, or target an existing endpoint when `OPENSEARCH_ENDPOINT` is configured.

When Nori is available, mappings use a Korean analyzer. When it is not available, the mapping falls back to standard analysis plus keyword fields and alias expansion.

## Deployment Boundary

Cloudflare Pages hosts the static frontend. The backend is intentionally decoupled and can run locally or on a Lambda Function URL. Terraform creates private S3 storage and IAM policies by default, and can add the Lambda API when `deploy_api=true`; it does not create an always-on API host.
