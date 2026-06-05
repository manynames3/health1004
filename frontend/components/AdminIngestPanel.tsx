"use client";

import { CheckCircle2, DatabaseZap, FileUp, Loader2, LockKeyhole, RotateCcw, UploadCloud } from "lucide-react";
import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { fetchAdminStatus, ingestAdminFiles } from "../lib/api";
import { AdminIngestResponse, AdminStatus } from "../types";

const TOKEN_STORAGE_KEY = "health1004-admin-token";
const DEFAULT_BROWSER_UPLOAD_LIMIT_BYTES = 5 * 1024 * 1024;

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
  const uploadLimit = status?.upload_limit_bytes ?? DEFAULT_BROWSER_UPLOAD_LIMIT_BYTES;
  const hasAdminToken = adminToken.trim().length > 0;
  const hasFiles = files.length > 0;
  const exceedsUploadLimit = hasFiles && totalSize > uploadLimit;
  const ingestDisabledReason = !hasAdminToken
    ? "업로드하려면 ADMIN_TOKEN을 입력하세요."
    : !hasFiles
      ? "업로드할 PDF 파일을 하나 이상 선택하세요."
      : exceedsUploadLimit
        ? `선택한 PDF가 ${formatBytes(totalSize)}로 브라우저 업로드 한도 ${formatBytes(uploadLimit)}를 넘습니다. 대량 파일은 CLI/S3 업로드를 사용하세요.`
      : "";

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
      setError(err instanceof Error ? formatAdminError(err.message) : "관리자 상태를 확인할 수 없습니다.");
    } finally {
      setLoadingStatus(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!adminToken.trim() || files.length === 0 || exceedsUploadLimit) return;
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
      setError(adminIngestError(err, totalSize, uploadLimit));
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="admin-panel" aria-labelledby="admin-title">
      <div className="admin-copy">
        <p className="eyebrow">ADMIN</p>
        <h2 id="admin-title">PDF를 AWS에 업로드</h2>
        <p>
          한국어 PDF를 S3에 저장하고, 원문 조각과 문서 목록을 같은 처리 흐름으로 갱신합니다.
          브라우저 업로드는 소량 파일용이며, 대량 파일은 CLI/S3 업로드를 권장합니다.
        </p>
      </div>

      <form className="admin-form" onSubmit={onSubmit}>
        <div className="admin-field">
          <label htmlFor="admin-token">
            <LockKeyhole size={18} aria-hidden="true" />
            관리자 토큰
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
              강제 재처리
            </span>
          </label>
        </div>

        <label className="upload-dropzone" htmlFor="admin-pdfs">
          <UploadCloud size={28} aria-hidden="true" />
          <span>{files.length ? `PDF ${files.length}개 선택됨` : "PDF 파일 선택"}</span>
          <small>
            {files.length
              ? `${formatBytes(totalSize)} 선택됨 · 브라우저 한도 ${formatBytes(uploadLimit)}`
              : `${formatBytes(uploadLimit)}까지 여러 파일을 선택할 수 있습니다`}
          </small>
          <input id="admin-pdfs" type="file" accept="application/pdf,.pdf" multiple onChange={onFilesChange} />
        </label>

        {files.length > 0 && (
          <div className="selected-files" aria-label="선택한 파일">
            {files.slice(0, 6).map((file) => (
              <span key={`${file.name}-${file.size}`}>
                <FileUp size={15} aria-hidden="true" />
                {file.name}
              </span>
            ))}
            {files.length > 6 && <span>외 {files.length - 6}개</span>}
          </div>
        )}

        {error && <div className="error-box">{error}</div>}

        <div className="admin-actions">
          {ingestDisabledReason && !uploading && (
            <p className="admin-action-hint" id="ingest-disabled-reason">
              {ingestDisabledReason}
            </p>
          )}
          <button className="secondary-admin-button" type="button" onClick={onCheckStatus} disabled={loadingStatus || !hasAdminToken}>
            {loadingStatus ? <Loader2 className="spin" size={18} /> : <CheckCircle2 size={18} />}
            상태 확인
          </button>
          <button
            className="primary-admin-button"
            type="submit"
            disabled={uploading || !hasAdminToken || !hasFiles || exceedsUploadLimit}
            aria-describedby={ingestDisabledReason ? "ingest-disabled-reason" : undefined}
          >
            {uploading ? <Loader2 className="spin" size={18} /> : <UploadCloud size={18} />}
            파일 업로드
          </button>
        </div>

        {status && (
          <div className="admin-status-grid">
            <StatusItem label="S3 버킷" value={status.s3_bucket || "설정 안 됨"} />
            <StatusItem label="문서 목록" value={status.metadata_key} />
            <StatusItem label="벡터 묶음" value={status.vector_bundle_key} />
            <StatusItem label="업로드 한도" value={formatBytes(status.upload_limit_bytes)} />
          </div>
        )}

        {result && (
          <div className="ingest-result">
            <div className="result-heading">
              <div>
                <p className="eyebrow">RUN {result.run_id}</p>
                <h3>업로드 완료</h3>
              </div>
              <span>{result.successful_pdfs}개 처리됨</span>
            </div>
            <div className="admin-status-grid">
              <StatusItem label="파일" value={`${result.total_pdfs}`} />
              <StatusItem label="건너뜀" value={`${result.skipped_pdfs}`} />
              <StatusItem label="쪽수" value={`${result.pages_processed}`} />
              <StatusItem label="원문 조각" value={`${result.chunks_created}`} />
            </div>
            <div className="result-files">
              {result.files.map((file) => (
                <article key={`${file.filename}-${file.status}`}>
                  <strong>{file.filename}</strong>
                  <span>{file.status}</span>
                  <small>
                    {file.error ||
                      `${file.page_count ?? 0}쪽 · 원문 조각 ${file.chunk_count ?? 0}개 · ${
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

function adminIngestError(error: unknown, totalSize: number, uploadLimit: number): string {
  const message = error instanceof Error ? formatAdminError(error.message) : "파일을 업로드할 수 없습니다.";
  if (message === "Failed to fetch") {
    return `업로드 요청을 완료할 수 없습니다. 배포된 API의 브라우저 업로드 한도는 ${formatBytes(uploadLimit)}이고 선택한 파일은 ${formatBytes(totalSize)}입니다. 대량 PDF는 CLI/S3 업로드를 사용하세요.`;
  }
  return message;
}

function formatAdminError(message: string): string {
  if (message === "Invalid admin token") return "관리자 토큰이 올바르지 않습니다.";
  return message;
}
