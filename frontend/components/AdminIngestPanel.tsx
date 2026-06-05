"use client";

import { CheckCircle2, DatabaseZap, FileUp, Loader2, LockKeyhole, RotateCcw, UploadCloud } from "lucide-react";
import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { fetchAdminStatus, ingestAdminFiles } from "../lib/api";
import { AdminIngestResponse, AdminStatus } from "../types";

const TOKEN_STORAGE_KEY = "health1004-admin-token";

export function AdminIngestPanel() {
  const [adminToken, setAdminToken] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [s3Prefix, setS3Prefix] = useState("raw-pdfs/");
  const [force, setForce] = useState(false);
  const [status, setStatus] = useState<AdminStatus | null>(null);
  const [result, setResult] = useState<AdminIngestResponse | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (storedToken) setAdminToken(storedToken);
  }, []);

  const totalSize = useMemo(() => files.reduce((sum, file) => sum + file.size, 0), [files]);

  function onTokenChange(value: string) {
    setAdminToken(value);
    if (value) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, value);
    } else {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  }

  function onFilesChange(event: ChangeEvent<HTMLInputElement>) {
    setResult(null);
    setError("");
    setFiles(Array.from(event.target.files || []).filter((file) => file.name.toLowerCase().endsWith(".pdf")));
  }

  async function onCheckStatus() {
    setLoadingStatus(true);
    setError("");
    try {
      setStatus(await fetchAdminStatus(adminToken.trim()));
    } catch (err) {
      setStatus(null);
      setError(err instanceof Error ? err.message : "Could not check admin status.");
    } finally {
      setLoadingStatus(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!adminToken.trim() || files.length === 0) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await ingestAdminFiles({
          adminToken: adminToken.trim(),
          files,
          force,
          s3Prefix
        })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not ingest files.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="admin-panel" aria-labelledby="admin-title">
      <div className="admin-copy">
        <p className="eyebrow">ADMIN</p>
        <h2 id="admin-title">Ingest PDFs into AWS</h2>
        <p>
          Upload Korean PDF files, write source artifacts to S3, rebuild the vector bundle, and refresh the document
          manifest from the same ingestion pipeline used by the CLI.
        </p>
      </div>

      <form className="admin-form" onSubmit={onSubmit}>
        <div className="admin-field">
          <label htmlFor="admin-token">
            <LockKeyhole size={18} aria-hidden="true" />
            Admin token
          </label>
          <input
            id="admin-token"
            type="password"
            value={adminToken}
            onChange={(event) => onTokenChange(event.target.value)}
            placeholder="ADMIN_TOKEN"
            autoComplete="current-password"
          />
        </div>

        <div className="admin-row">
          <div className="admin-field">
            <label htmlFor="s3-prefix">
              <DatabaseZap size={18} aria-hidden="true" />
              S3 prefix
            </label>
            <input id="s3-prefix" value={s3Prefix} onChange={(event) => setS3Prefix(event.target.value)} />
          </div>
          <label className="admin-toggle">
            <input type="checkbox" checked={force} onChange={(event) => setForce(event.target.checked)} />
            <span>
              <RotateCcw size={18} aria-hidden="true" />
              Force reprocess
            </span>
          </label>
        </div>

        <label className="upload-dropzone" htmlFor="admin-pdfs">
          <UploadCloud size={28} aria-hidden="true" />
          <span>{files.length ? `${files.length} PDFs selected` : "Select PDF files"}</span>
          <small>{files.length ? formatBytes(totalSize) : "Multiple files supported"}</small>
          <input id="admin-pdfs" type="file" accept="application/pdf,.pdf" multiple onChange={onFilesChange} />
        </label>

        {files.length > 0 && (
          <div className="selected-files" aria-label="Selected files">
            {files.slice(0, 6).map((file) => (
              <span key={`${file.name}-${file.size}`}>
                <FileUp size={15} aria-hidden="true" />
                {file.name}
              </span>
            ))}
            {files.length > 6 && <span>{files.length - 6} more</span>}
          </div>
        )}

        {error && <div className="error-box">{error}</div>}

        <div className="admin-actions">
          <button className="secondary-admin-button" type="button" onClick={onCheckStatus} disabled={loadingStatus || !adminToken.trim()}>
            {loadingStatus ? <Loader2 className="spin" size={18} /> : <CheckCircle2 size={18} />}
            Check status
          </button>
          <button className="primary-admin-button" type="submit" disabled={uploading || !adminToken.trim() || files.length === 0}>
            {uploading ? <Loader2 className="spin" size={18} /> : <UploadCloud size={18} />}
            Ingest files
          </button>
        </div>

        {status && (
          <div className="admin-status-grid">
            <StatusItem label="S3 bucket" value={status.s3_bucket || "Not configured"} />
            <StatusItem label="Metadata" value={status.metadata_key} />
            <StatusItem label="Vector bundle" value={status.vector_bundle_key} />
            <StatusItem label="Upload limit" value={formatBytes(status.upload_limit_bytes)} />
          </div>
        )}

        {result && (
          <div className="ingest-result">
            <div className="result-heading">
              <div>
                <p className="eyebrow">RUN {result.run_id}</p>
                <h3>Ingestion complete</h3>
              </div>
              <span>{result.successful_pdfs} ingested</span>
            </div>
            <div className="admin-status-grid">
              <StatusItem label="Files" value={`${result.total_pdfs}`} />
              <StatusItem label="Skipped" value={`${result.skipped_pdfs}`} />
              <StatusItem label="Pages" value={`${result.pages_processed}`} />
              <StatusItem label="Chunks" value={`${result.chunks_created}`} />
            </div>
            <div className="result-files">
              {result.files.map((file) => (
                <article key={`${file.filename}-${file.status}`}>
                  <strong>{file.filename}</strong>
                  <span>{file.status}</span>
                  <small>
                    {file.error ||
                      `${file.page_count ?? 0} pages · ${file.chunk_count ?? 0} chunks · ${
                        file.extraction_method || "extraction"
                      }`}
                  </small>
                </article>
              ))}
            </div>
          </div>
        )}
      </form>
    </section>
  );
}

function StatusItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
