import pytest
from fastapi import HTTPException, Response

from app import main
from app.models import AdminAliasSuggestionRequest


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


def test_admin_alias_suggestion_stores_pending_suggestion(monkeypatch):
    class FakeStorage:
        def __init__(self, _settings):
            self.payload = {"suggestions": []}

        def get_json(self, key: str):
            assert key == main.ALIAS_SUGGESTIONS_KEY
            return self.payload

        def put_json(self, key: str, payload):
            assert key == main.ALIAS_SUGGESTIONS_KEY
            self.payload = payload

    fake = FakeStorage(None)
    monkeypatch.setattr(main, "S3Storage", lambda settings: fake)

    response = main.admin_alias_suggestion(
        AdminAliasSuggestionRequest(
            query="카라멜색소",
            category="substances",
            suggested_alias="카라멜색소",
            canonical_slug="caramel-color",
        )
    )

    assert response.status == "saved"
    assert fake.payload["suggestions"][0]["suggested_alias"] == "카라멜색소"
    assert fake.payload["suggestions"][0]["status"] == "pending"
