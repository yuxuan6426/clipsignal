import argparse
import asyncio
import os
import secrets
import threading
import time
import webbrowser
from pathlib import Path
from typing import Annotated, Literal

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .bridge import probe
from .models import (
    Capture, Creator, CreatorWorkLink, Creators, Current, Navigation, Page, ProfileNavigation, Search, ServiceError,
    Video, ViewState,
)
from .preview import canonical_share, read_public_preview
from .socialdatax import PREFIX as SOCIALDATAX_PREFIX, SocialDataX, configured_source
from .store import Store, normalize_share

WEB = Path(__file__).with_name("web")
PORT = 8765
DATA_DIR = Path(os.environ["CHANNELS_DATA_DIR"]) if "CHANNELS_DATA_DIR" in os.environ else (
    Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "ChannelsLocal"
)
Limit = Annotated[int, Query(ge=1, le=100)]


class Pair(BaseModel):
    key: str = Field(max_length=128)


class Ack(ViewState):
    command_id: str
    creator_id: str | None = None


class Open(BaseModel):
    reference: str = Field(max_length=2048)


class WorkLinkRequest(BaseModel):
    creator_id: str = Field(min_length=1, max_length=2048)
    video_id: str = Field(min_length=1, max_length=2048)


class Views:
    def __init__(self):
        self.lock = threading.Lock()
        self.tab = ""
        self.seen = 0.0
        self.view = ViewState()
        self.pending = None

    def active(self):
        if not self.tab or time.monotonic() - self.seen > 8:
            raise ServiceError(409, "NO_ACTIVE_VIEW", "请在浏览器标签页开启 Agent 联动。")
        return self.view

    def check_tab(self, tab):
        if self.tab != tab:
            raise ServiceError(409, "TAB_NOT_PAIRED", "该标签页未配对，或已被另一个标签页接管。")

    async def navigate(self, reference=None, direction=None, creator_id=None):
        with self.lock:
            state = self.active()
            if direction:
                if state.video_id not in state.playlist:
                    raise ServiceError(409, "NO_PLAYLIST", "当前视频不在观看列表里。")
                index = state.playlist.index(state.video_id) + (1 if direction == "next" else -1)
                if not 0 <= index < len(state.playlist):
                    raise ServiceError(409, "PLAYLIST_BOUNDARY", "已到当前列表边界。")
                reference = state.playlist[index]
            if self.pending:
                raise ServiceError(409, "NAVIGATION_IN_PROGRESS", "上一条导航仍在执行。")
            target = {"creator_id": creator_id} if creator_id else {"video_id": reference}
            command = {"id": secrets.token_hex(16), **target, "ack": False}
            self.pending = command
        try:
            for _ in range(1250 if creator_id and creator_id.startswith(SOCIALDATAX_PREFIX)
                           or reference and reference.startswith(SOCIALDATAX_PREFIX) else 50):
                await asyncio.sleep(0.1)
                with self.lock:
                    if command["ack"]:
                        if creator_id:
                            return ProfileNavigation(status="applied", creator_id=creator_id)
                        return Navigation(status="applied", video_id=reference)
                    if self.pending is not command:
                        break
            raise ServiceError(504, "NAVIGATION_TIMEOUT", "浏览器未确认导航，请检查当前标签页。")
        finally:
            with self.lock:
                if self.pending is command:
                    self.pending = None


def create_app(store: Store, token: str, pair_key: str, port: int, *, socialdatax: SocialDataX | None = None) -> FastAPI:
    origin = f"http://127.0.0.1:{port}"
    browser_cookie = secrets.token_urlsafe(32)
    pair_expires = time.monotonic() + 600
    views = Views()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    def provider():
        if socialdatax is None:
            raise ServiceError(503, "SOCIALDATAX_DISABLED", "请填写项目 .env 中的 SocialDataX API Key 并重启后端。")
        return socialdatax

    @app.exception_handler(ServiceError)
    async def service_error(_, error):
        return JSONResponse({"code": error.code, "message": str(error)}, status_code=error.status)

    @app.middleware("http")
    async def local_access(request, call_next):
        headers = request.headers
        if headers.get("host") != f"127.0.0.1:{port}" or headers.get("origin") not in {None, origin}:
            return JSONResponse({"code": "ORIGIN_DENIED"}, status_code=403)
        path = request.url.path
        if path.startswith("/api/"):
            agent = secrets.compare_digest(headers.get("authorization", "").encode(), ("Bearer " + token).encode())
            browser = secrets.compare_digest(request.cookies.get("channels_session", "").encode(), browser_cookie.encode())
            if request.method not in {"GET", "HEAD"} and not agent and headers.get("origin") != origin:
                return JSONResponse({"code": "ORIGIN_REQUIRED"}, status_code=403)
            if not (agent or browser or path == "/api/v1/session"):
                return JSONResponse({"code": "SESSION_REQUIRED"}, status_code=401)
            if path.startswith("/api/v1/view/") and not browser:
                return JSONResponse({"code": "BROWSER_REQUIRED"}, status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' https://finder.video.qq.com; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        return response

    @app.get("/")
    def home():
        return FileResponse(WEB / "index.html")

    @app.post("/api/v1/session")
    def session(body: Pair):
        nonlocal pair_key
        with views.lock:
            if not pair_key or not secrets.compare_digest(body.key.encode(), pair_key.encode()) or time.monotonic() > pair_expires:
                raise ServiceError(403, "PAIRING_EXPIRED", "请使用启动脚本重新打开本地页面。")
            pair_key = ""
        response = JSONResponse({"status": "connected"})
        response.set_cookie("channels_session", browser_cookie, httponly=True, samesite="strict", path="/")
        return response

    @app.post("/api/v1/capture", response_model=Video)
    def capture(selection: Capture):
        return store.capture(selection, probe())

    @app.get("/api/v1/videos", response_model=Search)
    def search(q: str = Query(default="", max_length=250), source: Literal["local", "socialdatax"] = "local",
               cursor: str | None = None):
        if source == "socialdatax":
            if not q.strip():
                raise ServiceError(422, "SEARCH_REQUIRED", "请输入视频号检索关键词。")
            return provider().search(q.strip(), cursor)
        if cursor:
            raise ServiceError(422, "LOCAL_SEARCH_CURSOR", "本地检索无需分页游标。")
        return Search(items=store.search(q))

    @app.get("/api/v1/video", response_model=Video)
    def video(reference: str = Query(max_length=2048)):
        if reference.startswith(SOCIALDATAX_PREFIX):
            return provider().detail(reference)
        try:
            return store.get(reference)[0]
        except ServiceError as error:
            if error.code != "VIDEO_NOT_CAPTURED" or not reference.lower().startswith("https:"):
                raise
            share = canonical_share(normalize_share(reference))
            if share is None:
                raise ServiceError(422, "UNSUPPORTED_PREVIEW_LINK", "请输入视频号分享菜单提供的短链接。") from None
        try:
            preview = read_public_preview(share)
        except ServiceError as error:
            if socialdatax is None or error.code != "PREVIEW_UNAVAILABLE":
                raise
            return socialdatax.detail(share, share_url=share)
        return store.save_preview(preview)

    @app.get("/api/v1/comments", response_model=Page)
    def comments(reference: str, cursor: str | None = None, limit: Limit = 30):
        if reference.startswith(SOCIALDATAX_PREFIX):
            return provider().comments(reference, None, cursor, limit)
        try:
            work, _ = store.get(reference)
        except ServiceError as error:
            if socialdatax is None or error.code != "VIDEO_NOT_CAPTURED" or not reference.lower().startswith("https:"):
                raise
            work = video(reference)
        if work.source == "socialdatax" or (cursor and cursor.startswith(SOCIALDATAX_PREFIX)):
            return provider().comments(work.id, work.share_url, cursor, limit)
        page = store.page(work.id, cursor, limit)
        if socialdatax is not None and page.coverage == "unavailable" and work.share_url and not cursor:
            share = canonical_share(normalize_share(work.share_url))
            if share:
                return socialdatax.comments(work.id, share, None, limit)
        return page

    @app.get("/api/v1/creators", response_model=Creators)
    def creators(q: str = Query(default="", max_length=250)):
        matches = {v.creator_id: v for v in store.search("") if q.strip().casefold() in v.author.casefold()}
        return Creators(items=[store.creator(creator_id) for creator_id in matches])

    @app.get("/api/v1/creator", response_model=Creator)
    def creator(creator_id: str):
        if creator_id.startswith(SOCIALDATAX_PREFIX):
            return provider().creator(creator_id)
        return store.creator(creator_id)

    @app.get("/api/v1/creator-videos", response_model=Search)
    def creator_videos(creator_id: str, cursor: str | None = None):
        if creator_id.startswith(SOCIALDATAX_PREFIX):
            return provider().creator_videos(creator_id, cursor)
        if cursor:
            raise ServiceError(422, "LOCAL_SEARCH_CURSOR", "本地作品列表无需分页游标。")
        return Search(items=store.creator_videos(creator_id))

    @app.post("/api/v1/creator-work-link", response_model=CreatorWorkLink)
    def creator_work_link(selection: WorkLinkRequest):
        creator_id, video_id = selection.creator_id, selection.video_id
        if creator_id.startswith(SOCIALDATAX_PREFIX):
            return provider().creator_work_link(creator_id, video_id)
        work, _ = store.get(video_id)
        if (
            work.id != video_id
            or work.source != "authorized_import"
            or work.creator_id != creator_id
            or store.creator(creator_id).profile_status != "linked"
        ):
            raise ServiceError(409, "WORK_LINK_UNAVAILABLE", "所选作品没有与该公开账号关联。")
        share_url = canonical_share(normalize_share(work.share_url)) if work.share_url else None
        if not share_url:
            raise ServiceError(409, "WORK_LINK_UNAVAILABLE", "该作品未提供可用的微信分享短链。")
        return CreatorWorkLink(
            creator_id=creator_id, video_id=video_id, title=work.title, share_url=share_url, source="authorized_import",
        )

    def find_comment(video_id, comment_id):
        _, items = store.get(video_id)
        for item in items:
            if item.id == comment_id:
                return item
        raise ServiceError(404, "COMMENT_UNKNOWN", "评论已失效，请刷新评论列表。")

    @app.get("/api/v1/replies", response_model=Page)
    def replies(video_id: str, comment_id: str, cursor: str | None = None, limit: Limit = 30):
        if comment_id.startswith(SOCIALDATAX_PREFIX):
            return provider().replies(video_id, comment_id, cursor, limit)
        item = find_comment(video_id, comment_id)
        if item.reply_count == 0:
            return Page(items=[], next_cursor=None, coverage="complete")
        return Page(items=[], next_cursor=None, coverage="unavailable", reason="尚未验证此评论的回复归属。")

    @app.get("/api/v1/commenter", response_model=Creator)
    def commenter(video_id: str, comment_id: str):
        if comment_id.startswith(SOCIALDATAX_PREFIX):
            return provider().commenter(video_id, comment_id)
        item = find_comment(video_id, comment_id)
        if item.profile_status == "linked" and item.creator_id:
            return store.creator(item.creator_id)
        if item.profile_status == "no_visible_entry":
            raise ServiceError(409, "PROFILE_ENTRY_UNAVAILABLE", "该评论缺少与公开视频号账号的明确关联。")
        raise ServiceError(409, "PROFILE_UNVERIFIED", "该评论显示视频号标识，主页与身份的关联尚未验证。")

    @app.get("/api/v1/current", response_model=Current)
    def current():
        with views.lock:
            state = views.active()
        if not state.video_id:
            raise ServiceError(409, "NO_CURRENT_VIDEO", "当前标签页未显示作品。")
        return Current(video=video(state.video_id), playback_state=state.playback_state)

    @app.post("/api/v1/open", response_model=Navigation)
    async def open_video(body: Open):
        if body.reference.startswith(SOCIALDATAX_PREFIX):
            provider()
            return await views.navigate(reference=body.reference)
        result, _ = store.get(body.reference)
        return await views.navigate(reference=result.id)

    @app.post("/api/v1/navigate", response_model=Navigation)
    async def navigate(direction: Literal["previous", "next"]):
        return await views.navigate(direction=direction)

    @app.post("/api/v1/navigate-user", response_model=ProfileNavigation)
    async def navigate_user(user_id: str):
        if not user_id.startswith(SOCIALDATAX_PREFIX) and store.creator(user_id).profile_status != "linked":
            raise ServiceError(409, "PROFILE_UNVERIFIED", "当前记录缺少与公开账号的明确关联。")
        if user_id.startswith(SOCIALDATAX_PREFIX):
            provider()
        return await views.navigate(creator_id=user_id)

    def tab_id(request):
        tab = request.headers.get("x-view-id", "")
        if len(tab) != 36:
            raise ServiceError(422, "INVALID_TAB", "浏览器标签标识无效。")
        return tab

    @app.post("/api/v1/view/pair")
    def pair(request: Request, state: ViewState):
        with views.lock:
            views.tab = tab_id(request)
            views.seen, views.view, views.pending = time.monotonic(), state, None
        return {"status": "paired"}

    @app.post("/api/v1/view/unpair")
    def unpair(request: Request):
        with views.lock:
            views.check_tab(tab_id(request))
            views.tab, views.pending = "", None
        return {"status": "unpaired"}

    @app.post("/api/v1/view/tick")
    def tick(request: Request, state: ViewState):
        with views.lock:
            views.check_tab(tab_id(request))
            views.seen, views.view = time.monotonic(), state
            command = views.pending
            return {"command": {key: value for key, value in command.items() if key != "ack"}
                    if command and not command["ack"] else None}

    @app.post("/api/v1/view/ack")
    def ack(request: Request, state: Ack):
        with views.lock:
            views.check_tab(tab_id(request))
            command = views.pending
            target_matches = command and (
                state.creator_id == command["creator_id"] if "creator_id" in command
                else state.video_id == command["video_id"]
            )
            if not target_matches or state.command_id != command["id"]:
                raise ServiceError(409, "COMMAND_EXPIRED", "该导航指令已失效。")
            views.seen, views.view = time.monotonic(), state
            command["ack"] = True
        return {"status": "acknowledged"}

    app.mount("/assets", StaticFiles(directory=WEB), name="assets")
    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    token_file = DATA_DIR / f"mcp-{args.port}.token"
    store = Store(DATA_DIR / "channels.sqlite3")
    try:
        with token_file.open("x", encoding="ascii") as handle:
            handle.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    token = token_file.read_text(encoding="ascii").strip()
    if len(token) < 32:
        raise SystemExit("本地令牌无效。关闭服务后移除令牌文件，再重新启动。")
    pair_key = secrets.token_urlsafe(32)
    url = f"http://127.0.0.1:{args.port}/#connect={pair_key}"
    if not args.no_browser:
        threading.Timer(1.7, lambda: webbrowser.open(url)).start()
    print(f"在浏览器打开 {url}", flush=True)
    uvicorn.run(create_app(store, token, pair_key, args.port, socialdatax=configured_source()), host="127.0.0.1",
                port=args.port, access_log=False)


if __name__ == "__main__":
    main()
