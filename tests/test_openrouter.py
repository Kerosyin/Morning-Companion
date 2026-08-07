import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.openrouter import OpenRouterProvider

pytestmark = pytest.mark.asyncio


def _fake_settings():
    return MagicMock(
        openrouter_api_key="k",
        model="m",
        proxy=None,
        ai_request_timeout_seconds=30,
    )


def _make_response(status=200, json_data=None, text="{}"):
    response = AsyncMock()
    response.status = status
    response.json = AsyncMock(return_value=json_data or {})
    response.text = AsyncMock(return_value=text)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


def _patch_session(monkeypatch, response):
    monkeypatch.setattr("app.ai.openrouter.get_settings", lambda: _fake_settings())
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    return patch("app.ai.openrouter.aiohttp.ClientSession", return_value=mock_session)


async def test_content_present_returned(monkeypatch):
    response = _make_response(
        200, {"choices": [{"message": {"content": "Hello!"}}]}
    )

    with _patch_session(monkeypatch, response):
        provider = OpenRouterProvider()
        result = await provider._request([{"role": "user", "content": "hi"}])

    assert result == "Hello!"


async def test_content_null_returns_empty_string(monkeypatch):
    """Bug 14: a model may return content=None (reasoning/filtering);
    the provider must return '' rather than forwarding None to answer()."""
    response = _make_response(
        200, {"choices": [{"message": {"content": None}}]}
    )

    with _patch_session(monkeypatch, response):
        provider = OpenRouterProvider()
        result = await provider._request([{"role": "user", "content": "hi"}])

    assert result == ""


async def test_non_retryable_4xx_raises_immediately(monkeypatch):
    """Bug 10: a 4xx (401/400/...) must raise at once — NOT be retried 3 times
    with exponential backoff (would waste ~7-21s per request on a bad key)."""
    response = _make_response(401, text="unauthorized")

    with _patch_session(monkeypatch, response):
        provider = OpenRouterProvider()
        with pytest.raises(RuntimeError, match="401"):
            await provider._request([{"role": "user", "content": "hi"}])

    response.json.assert_not_called()
