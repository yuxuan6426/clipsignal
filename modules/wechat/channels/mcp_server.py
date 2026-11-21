import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Annotated, Literal

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from .models import Creator, CreatorWorkLink, Current, Navigation, Page, ProfileNavigation, Search, Video
from .server import DATA_DIR, PORT

mcp = FastMCP("wechat_channels_local")
Limit = Annotated[int, Field(ge=1, le=100)]
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
PUBLIC_READ = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True)
EXTERNAL_READ = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
NAVIGATION = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)
EXTERNAL_NAVIGATION = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
PROVIDER_TIMEOUT = 130


def call(path, query=None, body=None, *, post=False, timeout=8):
    port = int(os.getenv("CHANNELS_PORT", str(PORT)))
    try:
        token = (DATA_DIR / f"mcp-{port}.token").read_text(encoding="ascii").strip()
        with httpx.Client(base_url=f"http://127.0.0.1:{port}/api/v1/", trust_env=False, timeout=timeout) as client:
            result = client.request("POST" if post else "GET", path, params=query, json=body,
                                    headers={"Authorization": "Bearer " + token})
    except (OSError, httpx.HTTPError) as error:
        raise ToolError("BACKEND_UNAVAILABLE: 请先启动 Windows 本地服务。") from error
    payload = result.json()
    if result.is_error:
        raise ToolError(f"{payload.get('code', 'REQUEST_FAILED')}: {payload.get('message', '请检查工具参数。')}")
    return payload


@mcp.tool(annotations=EXTERNAL_READ)
def search_videos(query: str, source: Literal["local", "socialdatax"] = "local", cursor: str | None = None) -> Search:
    """Search the local library (default) or explicitly query SocialDataX using credits. Use a cursor with the same search."""
    return Search.model_validate(call("videos", {"q": query, "source": source, **({"cursor": cursor} if cursor else {})},
                                      timeout=PROVIDER_TIMEOUT if source == "socialdatax" else 8))


@mcp.tool(annotations=PUBLIC_READ)
def get_video_detail(reference: str) -> Video:
    """Get a work by ID or share URL. Uses Tencent public preview first for new links and may fall back to enabled SocialDataX."""
    return Video.model_validate(call("video", {"reference": reference}, timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=EXTERNAL_READ)
def get_video_comments(reference: str, cursor: str | None = None, limit: Limit = 30) -> Page:
    """Read a work's comments, using enabled SocialDataX credits if a public preview lacks comments. Use the same work for paging."""
    query = {"reference": reference, "limit": limit}
    if cursor:
        query["cursor"] = cursor
    return Page.model_validate(call("comments", query, timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=EXTERNAL_READ)
def get_comment_replies(video_id: str, comment_id: str, cursor: str | None = None, limit: Limit = 30) -> Page:
    """Check replies tied to this exact comment; unavailable if the client cannot verify them."""
    query = {"video_id": video_id, "comment_id": comment_id, "limit": limit}
    if cursor:
        query["cursor"] = cursor
    return Page.model_validate(call("replies", query, timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=EXTERNAL_READ)
def get_creator_profile(creator_id: str) -> Creator:
    """Get public profile data for a linked account or the author name shown on a work."""
    return Creator.model_validate(call("creator", {"creator_id": creator_id}, timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=EXTERNAL_READ)
def get_creator_videos(creator_id: str, cursor: str | None = None) -> Search:
    """List public works from the same source as the linked account. SocialDataX pages may consume credits."""
    query = {"creator_id": creator_id, **({"cursor": cursor} if cursor else {})}
    return Search.model_validate(call("creator-videos", query, timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True))
def get_creator_work_share_link(creator_id: str, video_id: str) -> CreatorWorkLink:
    """Get a verified WeChat work share link for a selected result from get_creator_videos. SocialDataX may consume credits."""
    body = {"creator_id": creator_id, "video_id": video_id}
    return CreatorWorkLink.model_validate(call("creator-work-link", body=body, post=True, timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=EXTERNAL_READ)
def get_commenter_profile(video_id: str, comment_id: str) -> Creator:
    """Read the public account linked to the exact work and comment. SocialDataX profiles may consume credits."""
    return Creator.model_validate(call("commenter", {"video_id": video_id, "comment_id": comment_id},
                                       timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=EXTERNAL_NAVIGATION)
def open_video(reference: str) -> Navigation:
    """Show a captured video in the paired browser tab and wait for acknowledgement."""
    return Navigation.model_validate(call("open", body={"reference": reference}, post=True, timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=EXTERNAL_NAVIGATION)
def navigate_to_user(user_id: str) -> ProfileNavigation:
    """Show a linked account's public profile in the paired workbench tab."""
    return ProfileNavigation.model_validate(call("navigate-user", {"user_id": user_id}, post=True,
                                                 timeout=PROVIDER_TIMEOUT))


@mcp.tool(annotations=READ_ONLY)
def get_current_video() -> Current:
    """Read the work and playback status reported by the paired local tab."""
    return Current.model_validate(call("current"))


@mcp.tool(annotations=NAVIGATION)
def navigate_video(direction: Literal["previous", "next"]) -> Navigation:
    """Move within the paired tab's current result list and wait for acknowledgement."""
    return Navigation.model_validate(call("navigate", {"direction": direction}, post=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--schema", action="store_true")
    mode.add_argument("--codex-config", action="store_true")
    args = parser.parse_args()
    if args.schema:
        tools = asyncio.run(mcp.list_tools())
        print(json.dumps({"tools": [tool.model_dump(by_alias=True, exclude_none=True) for tool in tools]},
                         ensure_ascii=True, indent=2))
    elif args.codex_config:
        print("[mcp_servers.wechat_channels_local]")
        print("command = " + json.dumps(Path(sys.executable).as_posix(), ensure_ascii=False))
        print('args = ["-m", "channels.mcp_server"]')
        print("cwd = " + json.dumps(Path(__file__).resolve().parents[1].as_posix(), ensure_ascii=False))
        print("tool_timeout_sec = 150")
    else:
        mcp.run(transport="stdio")
