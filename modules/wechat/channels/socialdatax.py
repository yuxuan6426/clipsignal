import os
import re
import secrets
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

import httpx
from dotenv import dotenv_values

from .models import Comment, Creator, CreatorWorkLink, Page, Search, ServiceError, Video
from .preview import canonical_share

API = "https://mcp.socialdatax.com/socialdatax/api/v1/wechat/"
PREFIX = "sdx:"
FINDER_ID = re.compile(r"v2_[\w-]+@finder", flags=re.ASCII)


def configured_source() -> "SocialDataX | None":
    config = dotenv_values(Path(__file__).resolve().parents[1] / ".env", encoding="utf-8-sig", interpolate=False)
    enabled = os.environ.get("SOCIALDATAX_ENABLED", config.get("SOCIALDATAX_ENABLED") or "true")
    key = os.environ.get("SOCIALDATAX_API_KEY", config.get("SOCIALDATAX_API_KEY") or "").strip()
    if enabled.strip().lower() == "true" and key:
        return SocialDataX(key)
    return None


def display_time(value: int) -> str | None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return None
    try:
        return datetime.fromtimestamp(value, timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def account_reference(account_id):
    if isinstance(account_id, str) and FINDER_ID.fullmatch(account_id):
        return PREFIX + account_id
    return None


class SocialDataX:
    def __init__(self, key: str, *, transport: httpx.BaseTransport | None = None):
        self._key = key
        self._transport = transport
        self._lock = Lock()
        self._cursors = OrderedDict()
        self._comments = OrderedDict()
        self._video_targets = OrderedDict()
        self._details = OrderedDict()
        self._creator_work_titles = OrderedDict()
        self._work_links = OrderedDict()

    def _request(self, path: str, body: dict) -> dict:
        if not self._key.isascii() or any(char.isspace() for char in self._key):
            raise ServiceError(401, "SOCIALDATAX_AUTH", "请检查 .env 中的 SocialDataX API Key 格式。")
        try:
            with httpx.Client(base_url=API, timeout=60, trust_env=False, transport=self._transport) as client:
                response = client.post(path, json=body, headers={"Authorization": "Bearer " + self._key})
        except httpx.TimeoutException:
            raise ServiceError(504, "SOCIALDATAX_TIMEOUT", "SocialDataX 查询超时，请稍后重试。") from None
        except httpx.HTTPError:
            raise ServiceError(502, "SOCIALDATAX_FAILED", "SocialDataX 暂时无法返回数据。") from None

        try:
            payload = response.json()
        except ValueError:
            payload = None
        code = str(payload.get("code", "")) if isinstance(payload, dict) else ""
        status = response.status_code
        if status in (401, 403) or code == "1401":
            raise ServiceError(401, "SOCIALDATAX_AUTH", "SocialDataX 拒绝了认证，请检查 API Key。")
        if status == 402 or code in ("1004", "1402"):
            raise ServiceError(402, "SOCIALDATAX_BALANCE", "SocialDataX 积分不足。")
        if status == 429 or code == "1429":
            raise ServiceError(429, "SOCIALDATAX_RATE_LIMIT", "SocialDataX 查询频率过高，请稍后重试。")
        if not response.is_success or not isinstance(payload, dict) or code:
            raise ServiceError(502, "SOCIALDATAX_FAILED", "SocialDataX 未返回此查询的数据。")
        return payload

    @staticmethod
    def _unexpected():
        return ServiceError(502, "SOCIALDATAX_RESPONSE", "SocialDataX 返回的数据缺少所需字段。")

    def _remember(self, cache, key, value):
        with self._lock:
            cache[key] = value
            cache.move_to_end(key)
            if len(cache) > 4096:
                cache.popitem(last=False)

    def _read(self, cache, key):
        with self._lock:
            return cache.get(key)

    def _cursor(self, context, token, remaining=()):
        if not token and not remaining:
            return None
        reference = PREFIX + secrets.token_urlsafe(18)
        self._remember(self._cursors, reference, (context, token, remaining))
        return reference

    def _resume(self, context, cursor):
        if not cursor:
            return "", ()
        record = self._read(self._cursors, cursor)
        if not record or record[0] != context:
            raise ServiceError(409, "CURSOR_EXPIRED", "分页游标已失效或不属于这次查询，请从第一页开始。")
        return record[1:]

    def _items(self, data):
        items = data.get("items")
        token = data.get("next_page_token") or ""
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items) or not isinstance(token, str):
            raise self._unexpected()
        return items, token

    def _video(self, row, share_url=None):
        remote_id = row.get("object_id") or row.get("encrypted_object_id")
        author = row.get("author", {})
        description = row.get("description") or ""
        if not isinstance(remote_id, str) or not remote_id or not isinstance(author, dict) or not isinstance(description, str):
            raise self._unexpected()
        video_id = PREFIX + remote_id
        pair = self._object_target(row)
        if pair:
            self._remember(self._video_targets, video_id, pair)
        return Video(
            id=video_id, creator_id=account_reference(author.get("user_id")) or "display-author:" + video_id,
            title=next((line.strip()[:96] for line in description.splitlines() if line.strip()), "视频号作品"),
            description=description, author=author.get("name") or "视频号作者",
            published_display=display_time(row.get("publish_time")), share_url=share_url,
            observed_at=datetime.now(timezone.utc).isoformat(), source="socialdatax", playback="wechat" if share_url else "unavailable",
            author_avatar_url=author.get("avatar_url"), cover_url=row.get("cover_image_url"),
            comment_count_display=str(row["comment_count"]) if isinstance(row.get("comment_count"), int) else None,
        )

    @staticmethod
    def _object_target(row):
        fields = ("object_id", "object_nonce_id")
        if all(isinstance(row.get(field), str) and row[field] for field in fields):
            return {field: row[field] for field in fields}
        return None

    def detail(self, reference, *, share_url=None):
        cached = self._read(self._details, reference)
        if cached:
            return cached
        value = reference.removeprefix(PREFIX)
        key = "url" if share_url else "object_id" if value.isascii() and value.isdecimal() else "encrypted_object_id"
        row = self._request("video/detail", {key: share_url or value})
        video = self._video(row, share_url)
        self._remember(self._details, reference, video)
        self._remember(self._details, video.id, video)
        pair = self._object_target(row)
        if pair and reference.startswith(PREFIX):
            self._remember(self._video_targets, reference, pair)
        return video

    def search(self, query: str, cursor: str | None) -> Search:
        return self._works("video/search", {"keyword": query}, cursor)

    def creator(self, creator_id: str) -> Creator:
        user_id = self._user_id(creator_id)
        row = self._request("user/info", {"user_id": user_id})
        if row.get("user_id") != user_id or not row.get("name"):
            raise ServiceError(409, "SOCIALDATAX_PROFILE_UNVERIFIED", "来源未返回与该评论账号一致的公开资料。")
        return Creator(
            id=creator_id, nickname=row["name"], bio=row.get("bio"), avatar_url=row.get("avatar_url"),
            profile_status="linked", source="socialdatax", observed_at=datetime.now(timezone.utc).isoformat(),
        )

    def creator_videos(self, creator_id: str, cursor: str | None) -> Search:
        works = self._works("user/video/list", {"user_id": self._user_id(creator_id)}, cursor)
        for work in works.items:
            if work.creator_id == creator_id:
                self._remember(self._creator_work_titles, (creator_id, work.id), work.title)
        return works

    def creator_work_link(self, creator_id: str, video_id: str) -> CreatorWorkLink:
        user_id = self._user_id(creator_id)
        key = (creator_id, video_id)
        cached = self._read(self._work_links, key)
        if cached:
            return cached
        title = self._read(self._creator_work_titles, key)
        object_id = video_id.removeprefix(PREFIX)
        if title is None or not video_id.startswith(PREFIX) or not (object_id.isascii() and object_id.isdecimal()):
            raise ServiceError(409, "WORK_LINK_UNAVAILABLE", "请先列出该账号的作品并选择一条可分享的作品。")

        result = self._request("video/share/url", {"object_id": object_id})
        url = result.get("share_url")
        try:
            share_url = canonical_share(url) if isinstance(url, str) and url.startswith("https://weixin.qq.com/sph/") else None
        except ValueError:
            share_url = None
        if not share_url:
            raise ServiceError(409, "WORK_LINK_UNVERIFIED", "来源未返回有效的微信作品短链。")

        detail = self._request("video/detail", {"url": share_url})
        author = detail.get("author")
        if detail.get("object_id") != object_id or not isinstance(author, dict) or author.get("user_id") != user_id:
            raise ServiceError(409, "WORK_LINK_UNVERIFIED", "分享短链未能通过作品和作者的归属核对。")
        verified = CreatorWorkLink(
            creator_id=creator_id, video_id=video_id, title=title, share_url=share_url, source="socialdatax",
        )
        self._remember(self._work_links, key, verified)
        return verified

    def _works(self, path, params, cursor):
        context = (path, tuple(params.items()))
        token, _ = self._resume(context, cursor)
        if token:
            params["page_token"] = token
        items, next_token = self._items(self._request(path, params))
        return Search(scope="socialdatax", items=[self._video(item) for item in items],
                      next_cursor=self._cursor(context, next_token))

    @staticmethod
    def _user_id(reference):
        value = reference.removeprefix(PREFIX)
        if account_reference(value) != reference:
            raise ServiceError(422, "SOCIALDATAX_INVALID_ACCOUNT", "请使用工具返回的公开视频号账号 ID。")
        return value

    def comments(self, video_id, share_url, cursor, limit):
        def target():
            if share_url:
                return {"url": share_url}
            pair = self._read(self._video_targets, video_id)
            if not pair and video_id.startswith(PREFIX):
                self.detail(video_id)
                pair = self._read(self._video_targets, video_id)
            if not pair:
                raise ServiceError(409, "SOCIALDATAX_VIDEO_REFERENCE", "请先使用该作品的公开分享链接读取详情。")
            return pair

        return self._comment_page("video/comment/list", video_id, target, cursor, limit)

    def replies(self, video_id, comment_id, cursor, limit):
        _, target, remote_comment = self._comment_entry(video_id, comment_id)
        if not target:
            raise ServiceError(409, "SOCIALDATAX_VIDEO_REFERENCE", "来源未提供读取回复所需的作品标识。")
        return self._comment_page("video/comment/reply/list", video_id, lambda: {**target, "comment_id": remote_comment},
                                  cursor, limit, parent_id=comment_id)

    def _comment_page(self, path, video_id, target, cursor, limit, parent_id=None):
        context = (path, video_id, parent_id)
        token, remainder = self._resume(context, cursor)
        if not remainder:
            params = target()
            items, token = self._items(self._request(path, {**params, **({"page_token": token} if token else {})}))
            remainder = [self._comment(row, video_id, params) for row in items]
        rows = remainder[:limit]
        next_cursor = self._cursor(context, token, remainder[limit:])
        return Page(items=rows, next_cursor=next_cursor, coverage="partial", source="socialdatax", video_id=video_id,
                    reason="仅包含 SocialDataX 返回的公开评论。")

    def _comment(self, row, video_id, params):
        remote_id = row.get("comment_id")
        author = row.get("author") or {}
        if not isinstance(remote_id, str) or not remote_id or not isinstance(author, dict):
            raise self._unexpected()
        target = self._object_target(row)
        if "object_id" in params and target and target != self._object_target(params):
            raise self._unexpected()
        creator_id = account_reference(author.get("user_id"))
        comment_id = PREFIX + remote_id
        self._remember(self._comments, (video_id, comment_id),
                       (creator_id, target or self._object_target(params), remote_id))
        return Comment(id=comment_id, author=author.get("name") or "视频号用户", text=row.get("content") or "",
                       time_display=display_time(row.get("publish_time")), reply_count=row.get("reply_count"),
                       likes_display=str(row["like_count"]) if isinstance(row.get("like_count"), int) else None,
                       creator_id=creator_id, profile_status="linked" if creator_id else "no_visible_entry")

    def _comment_entry(self, video_id, comment_id):
        entry = self._read(self._comments, (video_id, comment_id))
        if not entry:
            raise ServiceError(404, "COMMENT_UNKNOWN", "请先读取这条作品的评论列表。")
        return entry

    def commenter(self, video_id, comment_id):
        creator_id, _, _ = self._comment_entry(video_id, comment_id)
        if not creator_id:
            raise ServiceError(409, "PROFILE_ENTRY_UNAVAILABLE", "该评论未提供可查询的公开视频号账号。")
        return self.creator(creator_id)
