import pytest
from fastapi import HTTPException, Response

from app import main


def test_unique_filename_deduplicates_pdf_names():
    used_names: set[str] = set()

    assert main.unique_filename("weekly.pdf", used_names) == "weekly.pdf"
    assert main.unique_filename("weekly.pdf", used_names) == "weekly-2.pdf"
    assert main.unique_filename("weekly.pdf", used_names) == "weekly-3.pdf"


def test_require_admin_accepts_admin_header(monkeypatch):
    monkeypatch.setattr(main.settings, "admin_token", "secret-token")

    assert main.require_admin(x_admin_token="secret-token") is None


def test_require_admin_accepts_bearer_token(monkeypatch):
    monkeypatch.setattr(main.settings, "admin_token", "secret-token")

    assert main.require_admin(authorization="Bearer secret-token") is None


def test_require_admin_rejects_missing_or_bad_token(monkeypatch):
    monkeypatch.setattr(main.settings, "admin_token", "secret-token")

    with pytest.raises(HTTPException) as exc_info:
        main.require_admin(x_admin_token="wrong")

    assert exc_info.value.status_code == 401


def test_require_admin_requires_configured_secret(monkeypatch):
    monkeypatch.setattr(main.settings, "admin_token", "")

    with pytest.raises(HTTPException) as exc_info:
        main.require_admin(x_admin_token="secret-token")

    assert exc_info.value.status_code == 503


def test_cache_archive_response_sets_public_cache_header():
    response = Response()

    main.cache_archive_response(response)

    assert response.headers["Cache-Control"] == main.ARCHIVE_CACHE_CONTROL
