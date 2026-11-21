import asyncio
import json
import os
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager

import httpx
import pytest
import uvicorn
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from playwright.async_api import async_playwright, expect

from channels.import_data import ImportBundle
from channels.models import Comment, ServiceError, Video
from channels.server import create_app
from channels.socialdatax import SocialDataX
from channels.store import Store

TOKEN = "test-token-for-the-loopback-test"
KEY = "one-time-test-browser-key"
SHARE = "https://weixin.qq.com/sph/TestingPreview"
WORK_SHARE = "https://weixin.qq.com/sph/PublicWork"


def import_sample():
    return {
        "schema_version": 1,
        "source_id": "fixture",
        "source": "授权样例",
        "exported_at": "2026-11-21T00:00:00Z",
        "profiles": [
            {"id": "real", "nickname": "同名账号", "bio": "公开简介",
             "profile_url": "https://weixin.qq.com/sph/PublicProfile"},
            {"id": "other", "nickname": "同名账号", "bio": "不同账号"},
        ],
        "videos": [
            {"id": "original", "title": "分享预览", "author": "作品作者", "share_url": SHARE,
             "comments_coverage": "partial", "comments": [
                 {"id": "1", "author": "同名账号", "text": "评论一", "account_id": "real"},
                 {"id": "2", "author": "同名账号", "text": "评论二", "account_id": "other"},
                 {"id": "3", "author": "同名账号", "text": "缺少关联"},
             ]},
            {"id": "other-work", "title": "评论者公开作品", "author": "同名账号", "share_url": WORK_SHARE,
             "account_id": "real", "comments_coverage": "complete", "comments": []},
            {"id": "no-link-work", "title": "缺少分享短链的作品", "author": "同名账号",
             "account_id": "other", "comments_coverage": "complete", "comments": []},
        ],
    }


async def call_tool(session, name, **args):
    result = await session.call_tool(name, args)
    assert not result.isError, result.content
    return result.structuredContent


@contextmanager
def backend(data_dir, seed, *, socialdatax=None):
    store = Store(data_dir / "channels.sqlite3")
    if seed:
        with store.connect() as db:
            for ident, title in [("a", "航天样本 A"), ("b", "航天样本 B")]:
                store.save(db, Video(id=ident, title=title, description=title,
                                    creator_id=f"creator-{ident}", author="样本作者",
                                    observed_at="2026-11-21T00:00:00+00:00", source="test_fixture"),
                           [Comment(id=f"{ident}-1", author="样本评论者", text="用于验收的评论。", reply_count=0),
                            Comment(id=f"{ident}-2", author="样本评论者", text="分页样本。", reply_count=0)])
        db.close()
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]
    (data_dir / f"mcp-{port}.token").write_text(TOKEN, encoding="ascii")
    server = uvicorn.Server(uvicorn.Config(create_app(store, TOKEN, KEY, port, socialdatax=socialdatax), host="127.0.0.1", port=port,
                                           access_log=False, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        assert server.started
        yield f"http://127.0.0.1:{port}", StdioServerParameters(
            command=sys.executable, args=["-m", "channels.mcp_server"],
            env={"CHANNELS_DATA_DIR": str(data_dir), "CHANNELS_PORT": str(port),
                 "PYTHONDONTWRITEBYTECODE": "1"},
        )
    finally:
        server.should_exit = True
        thread.join(6)


async def exercise(origin, parameters, channel, live):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(origin + "/#connect=" + KEY)
            if live:
                await page.get_by_text("从微信窗口读取", exact=True).click()
                async with page.expect_response(lambda r: r.url.endswith("/api/v1/capture"), timeout=40_000) as pending:
                    await page.get_by_role("button", name="读取视频与评论").click()
                response = await pending.value
                result = await response.json()
                assert response.ok, result.get("code")
                video_id = result["id"]
            else:
                await page.get_by_role("searchbox").fill("航天")
                await page.get_by_role("button", name="搜索", exact=True).click()
                await page.get_by_role("button", name="航天样本 B").click()
                video_id = "b"
            await expect(page.locator("#detail")).to_be_visible(timeout=35_000)
            await expect(page.locator("#comments li").first).to_be_visible()
            await page.get_by_role("button", name="开启 Agent 联动").click()
            await expect(page.get_by_role("button", name="关闭 Agent 联动")).to_be_visible()
            async with stdio_client(parameters) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    assert "get_creator_work_share_link" in {tool.name for tool in (await session.list_tools()).tools}

                    async def tool(name, arguments=None):
                        result = await session.call_tool(name, arguments or {})
                        assert not result.isError, name
                        return result.structuredContent

                    before = await tool("get_current_video")
                    detail = await tool("get_video_detail", {"reference": video_id})
                    assert before["video"] == detail
                    assert await page.locator("#author").text_content() == detail["author"]
                    creator = await tool("get_creator_profile", {"creator_id": detail["creator_id"]})
                    assert creator["nickname"] == detail["author"]
                    comments = await tool("get_video_comments", {"reference": video_id, "limit": 1})
                    first = comments["items"][0]
                    assert await page.locator("#comments li p").first.text_content() == first["text"]
                    hidden = await session.call_tool("get_commenter_profile", {"video_id": video_id, "comment_id": first["id"]})
                    assert hidden.isError and "PROFILE" in hidden.content[0].text
                    if not live:
                        assert (await tool("search_videos", {"query": "航天"}))["scope"] == "local"
                        cursor = comments["next_cursor"]
                        assert cursor
                        second = await tool("get_video_comments", {"reference": "b", "cursor": cursor, "limit": 1})
                        assert second["items"][0]["id"] == "b-2" and second["next_cursor"] is None
                        mismatched = await session.call_tool("get_video_comments", {"reference": "a", "cursor": cursor})
                        assert mismatched.isError and "CURSOR_EXPIRED" in mismatched.content[0].text
                        assert (await tool("navigate_video", {"direction": "next"}))["video_id"] == "a"
                        assert (await tool("open_video", {"reference": "b"}))["status"] == "applied"
                        await expect(page.locator("#title")).to_have_text("航天样本 B")
            await page.get_by_role("button", name="关闭 Agent 联动").click()
        finally:
            await browser.close()


@pytest.mark.parametrize("channel", ["chromium"])
def test_browser_and_mcp_share_data(tmp_path, channel):
    with backend(tmp_path, seed=True) as (origin, parameters):
        assert httpx.get(origin + "/api/v1/videos").status_code == 401
        assert httpx.get(origin + "/api/v1/videos", headers={"Origin": "https://example.org"}).status_code == 403
        asyncio.run(exercise(origin, parameters, channel, live=False))


def test_workbench_appearance_follows_system_and_remembers_choice(tmp_path):
    async def scenario(origin):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(color_scheme="light", viewport={"width": 390, "height": 844})
                await page.goto(origin + "/#connect=" + KEY)
                await expect(page.locator("html")).to_have_attribute("data-theme", "light")
                await page.emulate_media(color_scheme="dark")
                await expect(page.locator("html")).to_have_attribute("data-theme", "dark")
                await page.get_by_text("日间", exact=True).click()
                await expect(page.locator("html")).to_have_attribute("data-theme", "light")
                await page.reload()
                await expect(page.locator("html")).to_have_attribute("data-theme", "light")
                await expect(page.locator('input[value="light"]')).to_be_checked()
                await page.get_by_text("夜间", exact=True).click()
                await expect(page.locator("html")).to_have_attribute("data-theme", "dark")
                await page.emulate_media(color_scheme="light")
                await expect(page.locator("html")).to_have_attribute("data-theme", "dark")
                await page.get_by_text("系统", exact=True).click()
                await expect(page.locator("html")).to_have_attribute("data-theme", "light")
                await page.get_by_role("button", name="输入分享链接").click()
                await expect(page.get_by_role("searchbox")).to_be_focused()
                assert await page.evaluate("document.documentElement.scrollWidth === window.innerWidth")
            finally:
                await browser.close()

    with backend(tmp_path, seed=False) as (origin, _):
        asyncio.run(scenario(origin))


def test_free_headless_stdio(tmp_path, monkeypatch):
    calls = []

    def preview(share):
        calls.append(share)
        return Video(id="preview", creator_id="preview-author", title="分享预览", description="公开文案",
                     author="作品作者", share_url=SHARE, observed_at="2026-11-20T00:00:00+00:00",
                     comment_count_display="3", source="wechat_public_preview")

    def unexpected_probe():
        pytest.fail("后台读取调用了微信窗口")

    monkeypatch.setattr("channels.server.read_public_preview", preview)
    monkeypatch.setattr("channels.server.probe", unexpected_probe)

    async def scenario(parameters):
        async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
            await session.initialize()

            async def error(name, code, **args):
                result = await session.call_tool(name, args)
                assert result.isError and code in result.content[0].text

            alias = "https://channels.weixin.qq.com/finder-preview/pages/sph?id=TestingPreview"
            detail = await call_tool(session, "get_video_detail", reference=alias)
            assert detail["source"] == "wechat_public_preview" and calls == [SHARE]
            assert (await call_tool(session, "get_video_detail", reference=SHARE)) == detail
            search = await call_tool(session, "search_videos", query="分享预览")
            assert search == {"scope": "local", "items": [detail], "next_cursor": None}
            preview_page = await call_tool(session, "get_video_comments", reference=detail["id"])
            assert preview_page["coverage"] == "unavailable" and not preview_page["items"]
            await error("get_video_detail", "INVALID_SHARE_URL", reference="https://weixin.qq.com.example.org/sph/fake")

            bundle = import_sample()
            path = tmp_path / "import.json"
            path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
            process = await asyncio.to_thread(
                subprocess.run, [sys.executable, "-X", "utf8", "-m", "channels.import_data", str(path)],
                env={**os.environ, "CHANNELS_DATA_DIR": str(tmp_path)}, capture_output=True,
                encoding="utf-8", timeout=12,
            )
            assert process.returncode == 0, process.stderr
            imported = await call_tool(session, "get_video_detail", reference=alias)
            assert imported["id"] == detail["id"] and imported["source"] == "authorized_import"
            first = await call_tool(session, "get_video_comments", reference=SHARE, limit=1)
            assert first["coverage"] == "partial" and first["next_cursor"]

            store = Store(tmp_path / "channels.sqlite3")
            store.import_bundle(ImportBundle.model_validate(bundle))
            second = await call_tool(session, "get_video_comments", reference=SHARE, limit=2, cursor=first["next_cursor"])
            assert len(second["items"]) == 2 and second["next_cursor"] is None
            video_id = imported["id"]
            alice = await call_tool(session, "get_commenter_profile", video_id=video_id, comment_id=first["items"][0]["id"])
            other = await call_tool(session, "get_commenter_profile", video_id=video_id, comment_id=second["items"][0]["id"])
            assert alice["id"] != other["id"] and alice["nickname"] == other["nickname"]
            assert alice["profile_url"] == "https://weixin.qq.com/sph/PublicProfile"
            works = await call_tool(session, "get_creator_videos", creator_id=alice["id"])
            assert [item["title"] for item in works["items"]] == ["评论者公开作品"]
            work_id = works["items"][0]["id"]
            link = await call_tool(session, "get_creator_work_share_link", creator_id=alice["id"], video_id=work_id)
            assert link == {
                "creator_id": alice["id"], "video_id": work_id, "title": "评论者公开作品",
                "share_url": WORK_SHARE, "source": "authorized_import",
            }
            await error("get_creator_work_share_link", "WORK_LINK_UNAVAILABLE", creator_id=other["id"], video_id=work_id)
            other_works = await call_tool(session, "get_creator_videos", creator_id=other["id"])
            await error("get_creator_work_share_link", "WORK_LINK_UNAVAILABLE",
                        creator_id=other["id"], video_id=other_works["items"][0]["id"])
            await error("get_commenter_profile", "COMMENT_UNKNOWN",
                        video_id=works["items"][0]["id"], comment_id=first["items"][0]["id"])
            await error("get_commenter_profile", "PROFILE_ENTRY_UNAVAILABLE",
                        video_id=video_id, comment_id=second["items"][1]["id"])
            await error("navigate_to_user", "NO_ACTIVE_VIEW", user_id=alice["id"])

            bundle["videos"][0]["comments"][1]["text"] = "已更新评论"
            store.import_bundle(ImportBundle.model_validate(bundle))
            await error("get_video_comments", "CURSOR_EXPIRED", reference=SHARE, cursor=first["next_cursor"])
            bundle["profiles"][0]["bio"] = "事务回滚时不得保存"
            bundle["videos"][0]["title"] = "事务回滚时不得保存"
            bundle["videos"][1]["share_url"] = SHARE
            with pytest.raises(ServiceError, match="分享链接已关联"):
                store.import_bundle(ImportBundle.model_validate(bundle))
            assert (await call_tool(session, "get_video_detail", reference=SHARE))["title"] == "分享预览"
            assert (await call_tool(session, "get_creator_profile", creator_id=alice["id"]))["bio"] == "公开简介"
            assert calls == [SHARE]

    with backend(tmp_path, seed=False) as (_, parameters):
        asyncio.run(scenario(parameters))


def test_linked_commenter_profile_in_workbench(tmp_path):
    store = Store(tmp_path / "channels.sqlite3")
    store.import_bundle(ImportBundle.model_validate(import_sample()))

    async def scenario(origin, parameters):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(origin + "/#connect=" + KEY)
                await page.get_by_role("button", name="分享预览").click()
                await page.locator("#comments button").first.click()
                await expect(page.get_by_role("dialog")).to_be_visible()
                await expect(page.get_by_role("link", name="打开微信视频号主页")).to_have_attribute(
                    "href", "https://weixin.qq.com/sph/PublicProfile")
                await expect(page.get_by_role("link", name="打开微信作品")).to_have_count(0)
                await page.get_by_role("button", name="获取微信作品链接").click()
                await expect(page.get_by_role("link", name="打开微信作品")).to_have_attribute("href", WORK_SHARE)
                assert len(browser.contexts[0].pages) == 1
                await page.get_by_role("button", name="评论者公开作品").last.click()
                await expect(page.locator("#title")).to_have_text("评论者公开作品")
                await page.get_by_role("button", name="开启 Agent 联动").click()
                async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
                    await session.initialize()
                    video = await call_tool(session, "get_video_detail", reference=WORK_SHARE)
                    result = await call_tool(session, "navigate_to_user", user_id=video["creator_id"])
                    assert result == {"status": "applied", "creator_id": video["creator_id"]}
                await expect(page.get_by_role("dialog").get_by_text("公开简介")).to_be_visible()
            finally:
                await browser.close()

    with backend(tmp_path, seed=False) as (origin, parameters):
        asyncio.run(scenario(origin, parameters))


def test_socialdatax_live_contract_via_stdio(tmp_path, monkeypatch):
    def unexpected_probe():
        pytest.fail("SocialDataX 后台路径调用了微信窗口")

    monkeypatch.setattr("channels.server.probe", unexpected_probe)
    store = Store(tmp_path / "channels.sqlite3")
    store.save_preview(Video(id="viral", creator_id="preview-author", title="热门视频", description="公开预览",
                             author="作品作者", share_url=SHARE, observed_at="2026-11-21T00:00:00Z",
                             comment_count_display="1.2万", source="wechat_public_preview"))
    account_id = "v2_public123@finder"
    other_account = "v2_different456@finder"
    pair = {"object_id": "8001", "object_nonce_id": "nonce-8001"}
    token = "opaque-upstream/+token="
    calls = []
    share_issue = None

    def handle(request):
        assert request.url.host == "mcp.socialdatax.com"
        assert request.headers["Authorization"] == "Bearer fake-test-key"
        assert request.method == "POST"
        path = request.url.path.removeprefix("/socialdatax/api/v1/wechat/")
        payload = json.loads(request.content)
        calls.append((path, payload))
        if path == "video/search":
            assert payload == {"keyword": "热门"}
            return httpx.Response(200, json={"items": [
                {"encrypted_object_id": "export/abc123", "description": "热门作品", "author": {"name": "另一个作者"}},
            ], "next_page_token": ""})
        if path == "video/detail":
            if payload == {"url": WORK_SHARE}:
                return httpx.Response(200, json={
                    "object_id": "9002" if share_issue == "wrong-work" else pair["object_id"],
                    "author": {"user_id": other_account if share_issue == "wrong-author" else account_id},
                })
            assert payload == {"encrypted_object_id": "export/abc123"}
            return httpx.Response(200, json={**pair, "description": "热门作品", "author": {"name": "另一个作者"}})
        if path == "video/share/url":
            assert payload == {"object_id": pair["object_id"]}
            if share_issue == "provider-error":
                return httpx.Response(429, json={"code": 1429})
            if share_issue == "insufficient-balance":
                return httpx.Response(200, json={"code": 1004})
            url = "https://weixin.qq.com.example.org/sph/Foreign" if share_issue == "foreign-host" else WORK_SHARE
            return httpx.Response(200, json={"share_url": url})
        if path == "video/comment/list":
            assert payload in ({"url": SHARE}, {"url": SHARE, "page_token": token})
            items = [] if "page_token" in payload else [
                {**pair, "comment_id": "901", "content": "可关联账号", "author": {"name": "同名", "user_id": account_id}},
                {**pair, "comment_id": "902", "content": "普通微信用户", "author": {"name": "同名", "user_id": "x@stranger"}},
                {**pair, "comment_id": "903", "content": "资料不匹配", "author": {"name": "同名", "user_id": other_account}},
            ]
            return httpx.Response(200, json={"items": items, "next_page_token": token if items else ""})
        if path == "user/info":
            assert payload["user_id"] in {account_id, other_account}
            return httpx.Response(200, json={"user_id": account_id, "name": "公开视频号", "bio": "公开简介"})
        if path == "user/video/list":
            assert payload == {"user_id": account_id}
            return httpx.Response(200, json={"items": [
                {**pair, "description": "评论者的公开视频", "author": {"name": "公开视频号", "user_id": account_id}},
            ], "next_page_token": ""})
        if path == "video/comment/reply/list":
            assert payload == {**pair, "comment_id": "901"}
            return httpx.Response(200, json={"items": [], "next_page_token": ""})
        pytest.fail(f"Unexpected upstream request: {path}")

    async def scenario(parameters):
        nonlocal share_issue
        async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            local = await call_tool(session, "search_videos", query="热门")
            assert local["scope"] == "local" and local["items"][0]["id"] == "viral" and not calls
            work = await call_tool(session, "get_video_detail", reference=SHARE)
            assert work["source"] == "wechat_public_preview" and not calls
            page = await call_tool(session, "get_video_comments", reference=work["id"], limit=1)
            assert page["source"] == "socialdatax" and page["video_id"] == work["id"]
            first = page["items"][0]
            next_page = await call_tool(session, "get_video_comments", reference=SHARE, limit=2, cursor=page["next_cursor"])
            assert [path for path, _ in calls] == ["video/comment/list"]
            assert next_page["items"][0]["profile_status"] == "no_visible_entry"

            async def error(name, code, **values):
                result = await session.call_tool(name, values)
                assert result.isError and code in result.content[0].text

            await error("get_commenter_profile", "COMMENT_UNKNOWN", video_id="different-work", comment_id=first["id"])
            await error("get_commenter_profile", "PROFILE_ENTRY_UNAVAILABLE", video_id=work["id"],
                        comment_id=next_page["items"][0]["id"])
            await error("get_commenter_profile", "PROFILE_UNVERIFIED", video_id=work["id"],
                        comment_id=next_page["items"][1]["id"])
            account = await call_tool(session, "get_commenter_profile", video_id=work["id"], comment_id=first["id"])
            assert account["id"] == first["creator_id"] and account["profile_url"] is None
            work_args = {"creator_id": account["id"], "video_id": "sdx:8001"}
            await error("get_creator_work_share_link", "WORK_LINK_UNAVAILABLE", **work_args)
            works = await call_tool(session, "get_creator_videos", creator_id=account["id"])
            assert works["scope"] == "socialdatax" and works["items"][0]["title"] == "评论者的公开视频"
            initial_calls = len(calls)
            await error("get_creator_work_share_link", "WORK_LINK_UNAVAILABLE",
                        creator_id="sdx:" + other_account, video_id=work_args["video_id"])
            await error("get_creator_work_share_link", "WORK_LINK_UNAVAILABLE",
                        creator_id=account["id"], video_id="sdx:9999")
            assert len(calls) == initial_calls
            for share_issue, code, expected_paths in [
                ("provider-error", "SOCIALDATAX_RATE_LIMIT", ["video/share/url"]),
                ("insufficient-balance", "SOCIALDATAX_BALANCE", ["video/share/url"]),
                ("foreign-host", "WORK_LINK_UNVERIFIED", ["video/share/url"]),
                ("wrong-work", "WORK_LINK_UNVERIFIED", ["video/share/url", "video/detail"]),
                ("wrong-author", "WORK_LINK_UNVERIFIED", ["video/share/url", "video/detail"]),
            ]:
                start = len(calls)
                await error("get_creator_work_share_link", code, **work_args)
                assert [path for path, _ in calls[start:]] == expected_paths
            share_issue = None
            start = len(calls)
            verified = await call_tool(session, "get_creator_work_share_link", **work_args)
            assert verified["share_url"] == WORK_SHARE and verified["source"] == "socialdatax"
            assert verified == await call_tool(session, "get_creator_work_share_link", **work_args)
            assert calls[start:] == [("video/share/url", {"object_id": "8001"}), ("video/detail", {"url": WORK_SHARE})]
            reply = await call_tool(session, "get_comment_replies", video_id=work["id"], comment_id=first["id"])
            assert reply["source"] == "socialdatax"
            last = await call_tool(session, "get_video_comments", reference=work["id"], cursor=next_page["next_cursor"])
            assert last["items"] == [] and not last["next_cursor"]
            remote = await call_tool(session, "search_videos", query="热门", source="socialdatax")
            detail = await call_tool(session, "get_video_detail", reference=remote["items"][0]["id"])
            assert detail["id"] == "sdx:8001" and detail["source"] == "socialdatax"

    with backend(tmp_path, seed=False, socialdatax=SocialDataX("fake-test-key", transport=httpx.MockTransport(handle))) as (_, parameters):
        asyncio.run(scenario(parameters))


@pytest.mark.skipif(os.getenv("CHANNELS_LIVE_TEST") != "1", reason="requires open WeChat Channels comments")
@pytest.mark.parametrize("channel", ["chromium"])
def test_live_wechat_browser_and_mcp(tmp_path, channel):
    with backend(tmp_path, seed=False) as (origin, parameters):
        asyncio.run(exercise(origin, parameters, channel, live=True))
