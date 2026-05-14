from httpx import ASGITransport, AsyncClient
from src.main import app


async def test_chat_stream_no_api_key():
    """Chat stream should connect even if the upstream LLM call fails."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/chat/stream", json={"message": "hello"})
        # SSE response should connect; content may fail due to missing API key
        assert res.status_code == 200
