"""Verify the private fixture via a real loopback backend and MCP stdio."""
import asyncio
import secrets
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

import uvicorn
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from channels.models import Comment, Video
from channels.server import create_app
from channels.store import Store


async def verify(port, folder):
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "channels.mcp_server"],
        cwd=str(ROOT),
        env={"CHANNELS_DATA_DIR": str(folder), "CHANNELS_PORT": str(port),
             "SOCIALDATAX_ENABLED": "false"},
    )
    async with stdio_client(server) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            assert "get_video_comments" in {tool.name for tool in (await session.list_tools()).tools}
            detail = await session.call_tool("get_video_detail", {"reference": "fixture"})
            assert not detail.isError and detail.structuredContent["title"] == "Example work"
            comments = await session.call_tool("get_video_comments", {"reference": "fixture"})
            assert not comments.isError
            assert "Synthetic comment" in comments.model_dump_json()


with tempfile.TemporaryDirectory() as directory:
    folder = Path(directory)
    store = Store(folder / "channels.sqlite3")
    database = store.connect()
    try:
        with database:
            store.save(database, Video(id="fixture", title="Example work", description="Sample",
                                        creator_id="sample-creator", author="Sample",
                                        observed_at="2026-11-21T00:00:00Z", source="test_fixture"),
                       [Comment(id="one", author="Example", text="Synthetic comment", reply_count=0)])
    finally:
        database.close()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    token = secrets.token_hex()
    (folder / f"mcp-{port}.token").write_text(token, encoding="ascii")
    app = create_app(store, token, secrets.token_hex(), port)
    server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        assert server.started
        asyncio.run(asyncio.wait_for(verify(port, folder), timeout=15))
        print("WeChat synthetic detail and comments passed via MCP")
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()
