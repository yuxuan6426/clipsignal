import base64
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from .models import Capture, Comment, Creator, Page, ServiceError, Video
from .preview import canonical_share

if TYPE_CHECKING:
    from .import_data import ImportBundle

PREVIEW_REASON = "微信公开预览仅提供评论计数。此作品的评论可通过授权记录导入。"
UIA_REASON = "仅包含读取时微信评论面板已加载且可识别的内容。"


def normalize_share(value: str) -> str:
    try:
        parts = urlsplit(value.strip())
        allowed = (
            parts.scheme == "https"
            and parts.netloc.lower() in {"weixin.qq.com", "channels.weixin.qq.com"}
            and parts.path not in {"", "/"}
            and not any(c.isspace() or ord(c) < 32 or c == "\\" for c in value)
        )
    except ValueError:
        allowed = False
    if not allowed:
        raise ServiceError(422, "INVALID_SHARE_URL", "请输入微信分享菜单提供的 HTTPS 链接。")
    return urlunsplit(("https", parts.netloc.lower(), parts.path, parts.query, ""))


def imported_id(kind: str, *keys: str) -> str:
    encoded = json.dumps(keys, ensure_ascii=False).encode("utf-8")
    return kind + "-" + sha256(encoded).hexdigest()[:32]


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with closing(self.connect()) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY, share TEXT UNIQUE, video TEXT NOT NULL, comments TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY, profile TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS imported_videos (
                source_id TEXT NOT NULL, source_video_id TEXT NOT NULL, video_id TEXT NOT NULL UNIQUE,
                PRIMARY KEY (source_id, source_video_id)
            )""")

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def _snapshot(self, reference: str):
        with closing(self.connect()) as db:
            if reference.lower().startswith("https:"):
                row = self._by_share(db, normalize_share(reference))
            else:
                row = db.execute("SELECT video, comments FROM videos WHERE id = ?", (reference,)).fetchone()
        if row is None:
            raise ServiceError(404, "VIDEO_NOT_CAPTURED", "请先按公开分享链接读取作品，或导入授权记录。")
        video = Video.model_validate_json(row[0])
        snapshot = json.loads(row[1])
        if isinstance(snapshot, list):
            coverage = "complete" if video.source == "test_fixture" else "partial"
            reason = None if coverage == "complete" else UIA_REASON
            revision = video.observed_at
            rows = snapshot
        else:
            coverage, reason, rows = snapshot["coverage"], snapshot["reason"], snapshot["items"]
            revision = sha256(row[1].encode("utf-8")).hexdigest()
        return video, [Comment.model_validate(item) for item in rows], coverage, reason, revision

    def get(self, reference: str) -> tuple[Video, list[Comment]]:
        video, items, _, _, _ = self._snapshot(reference)
        return video, items

    @staticmethod
    def _by_share(db, share):
        row = db.execute("SELECT video, comments FROM videos WHERE share = ?", (share,)).fetchone()
        canonical = canonical_share(share)
        if row is None and canonical and canonical != share:
            row = db.execute("SELECT video, comments FROM videos WHERE share = ?", (canonical,)).fetchone()
        return row

    def save_preview(self, video: Video) -> Video:
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = self._by_share(db, video.share_url)
            if row:
                return Video.model_validate_json(row[0])
            self.save(db, video, [], coverage="unavailable", reason=PREVIEW_REASON)
        return video

    def capture(self, selection: Capture, observed: tuple[str, str, str | None, list[Comment]]) -> Video:
        author, description, published, comments = observed
        share = normalize_share(selection.share_url) if selection.share_url else None
        if share and selection.refresh_id:
            raise ServiceError(422, "CAPTURE_REFERENCE_CONFLICT", "请分别使用分享链接读取或按作品 ID 刷新。")
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = None
            if selection.refresh_id:
                row = db.execute("SELECT video FROM videos WHERE id = ?", (selection.refresh_id,)).fetchone()
                if row is None:
                    raise ServiceError(404, "VIDEO_NOT_CAPTURED", "找不到要刷新的作品。")
            elif share:
                row = self._by_share(db, share)
            previous = Video.model_validate_json(row[0]) if row else None
            if previous and previous.source != "wechat_uia":
                raise ServiceError(409, "CAPTURE_SOURCE_CONFLICT", "此作品已由后台数据源保存。")
            if previous and (previous.author, previous.description) != (author, description):
                raise ServiceError(409, "VIDEO_CHANGED", "当前微信评论区与已保存作品不同。")
            share = share or (previous.share_url if previous else None)
            revision = datetime.now(timezone.utc).isoformat()
            video = Video(
                id=previous.id if previous else uuid4().hex,
                creator_id=previous.creator_id if previous else uuid4().hex,
                author=author, title=description.splitlines()[0][:96], description=description,
                published_display=published, share_url=share, observed_at=revision,
            )
            # Comment references are snapshot-local. The same nickname never resolves an account.
            rows = [comment.model_copy(update={"id": f"{revision}/{comment.id}"}) for comment in comments]
            self.save(db, video, rows)
        return video

    def save(self, db, video: Video, comments: list[Comment], *, coverage=None, reason=None) -> None:
        rows = [item.model_dump() for item in comments]
        snapshot = rows if coverage is None else {"coverage": coverage, "reason": reason, "items": rows}
        db.execute("""INSERT INTO videos (id, share, video, comments) VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET share=excluded.share, video=excluded.video, comments=excluded.comments""",
            (video.id, video.share_url, video.model_dump_json(), json.dumps(snapshot, ensure_ascii=False)))

    def import_bundle(self, bundle: "ImportBundle") -> None:
        stamp = bundle.exported_at.astimezone(timezone.utc).isoformat()
        accounts = {
            profile.id: Creator(
                id=imported_id("account", bundle.source_id, profile.id), nickname=profile.nickname,
                bio=profile.bio, profile_url=normalize_share(profile.profile_url) if profile.profile_url else None,
                profile_status="linked", source="authorized_import", data_source=bundle.source, observed_at=stamp,
            )
            for profile in bundle.profiles
        }
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            for account in accounts.values():
                db.execute("""INSERT INTO profiles (id, profile) VALUES (?, ?)
                    ON CONFLICT(id) DO UPDATE SET profile=excluded.profile
                    WHERE json_extract(excluded.profile, '$.observed_at') >= json_extract(profiles.profile, '$.observed_at')""",
                           (account.id, account.model_dump_json()))
            for item in bundle.videos:
                self._import_video(db, bundle.source_id, bundle.source, stamp, accounts, item)

    def _import_video(self, db, source_id, source, stamp, accounts, item):
        share = normalize_share(item.share_url) if item.share_url else None
        row = self._by_share(db, share) if share else None
        share = (canonical_share(share) or share) if share else None
        if row is None and share:
            row = self._by_share(db, share)
        previous = Video.model_validate_json(row[0]) if row else None
        known = db.execute("""SELECT imported_videos.video_id, videos.video FROM imported_videos
            JOIN videos ON videos.id = imported_videos.video_id
            WHERE source_id = ? AND source_video_id = ?""", (source_id, item.id)).fetchone()
        if previous and (not known or known[0] != previous.id) and previous.source != "wechat_public_preview":
            raise ServiceError(409, "IMPORT_SHARE_CONFLICT", "分享链接已关联到其他本地记录。")
        if known and previous and previous.id != known[0]:
            raise ServiceError(409, "IMPORT_SHARE_CONFLICT", "分享链接已关联到另一条作品。")
        if known and Video.model_validate_json(known[1]).observed_at > stamp:
            raise ServiceError(409, "IMPORT_OLDER_SNAPSHOT", "来源文件早于已导入的作品记录。")
        video_id = known[0] if known else previous.id if previous else imported_id("video", source_id, item.id)
        creator = accounts.get(item.account_id)
        video = Video(
            id=video_id, title=item.title, description=item.description, author=item.author,
            creator_id=creator.id if creator else imported_id("display-author", video_id),
            observed_at=stamp, published_display=item.published_display, share_url=share,
            source="authorized_import", data_source=source,
            playback="wechat" if share else "unavailable",
            cover_url=previous.cover_url if previous else None,
            author_avatar_url=previous.author_avatar_url if previous else None,
            comment_count_display=previous.comment_count_display if previous else None,
        )
        rows = [
            Comment(
                id=imported_id("comment", video_id, comment.id), author=comment.author, text=comment.text,
                time_display=comment.time_display, likes_display=comment.likes_display, reply_count=comment.reply_count,
                creator_id=accounts[comment.account_id].id if comment.account_id else None,
                profile_status="linked" if comment.account_id else "no_visible_entry",
            )
            for comment in item.comments
        ]
        reasons = {"partial": "仅包含授权文件提供的部分评论。", "unavailable": "授权文件未提供评论数据。"}
        self.save(db, video, rows, coverage=item.comments_coverage, reason=reasons.get(item.comments_coverage))
        db.execute("""INSERT INTO imported_videos (source_id, source_video_id, video_id)
            VALUES (?, ?, ?) ON CONFLICT(source_id, source_video_id) DO NOTHING""", (source_id, item.id, video_id))

    def search(self, query: str) -> list[Video]:
        with closing(self.connect()) as db:
            rows = db.execute("SELECT video FROM videos ORDER BY rowid DESC").fetchall()
        terms = query.casefold().split()
        videos = (Video.model_validate_json(raw) for (raw,) in rows)
        return [v for v in videos if all(t in f"{v.title} {v.description} {v.author}".casefold() for t in terms)][:150]

    def creator(self, creator_id: str) -> Creator:
        with closing(self.connect()) as db:
            profile = db.execute("SELECT profile FROM profiles WHERE id = ?", (creator_id,)).fetchone()
            if profile:
                return Creator.model_validate_json(profile[0])
            row = db.execute("SELECT video FROM videos WHERE json_extract(video, '$.creator_id') = ?",
                             (creator_id,)).fetchone()
        if row is None:
            raise ServiceError(404, "CREATOR_UNKNOWN", "找不到本地作者记录。")
        video = Video.model_validate_json(row[0])
        return Creator(id=video.creator_id, nickname=video.author, source=video.source, data_source=video.data_source,
                       avatar_url=video.author_avatar_url, observed_at=video.observed_at)

    def creator_videos(self, creator_id: str) -> list[Video]:
        if self.creator(creator_id).profile_status != "linked":
            raise ServiceError(409, "CREATOR_WORKS_UNAVAILABLE", "当前资料缺少已关联的视频号账号。")
        with closing(self.connect()) as db:
            rows = db.execute("""SELECT video FROM videos WHERE json_extract(video, '$.creator_id') = ?
                ORDER BY rowid DESC LIMIT 150""", (creator_id,)).fetchall()
        return [Video.model_validate_json(raw) for (raw,) in rows]

    def page(self, reference: str, cursor: str | None, limit: int) -> Page:
        video, items, coverage, reason, revision = self._snapshot(reference)
        revision_key = f"{video.id}/{revision}"
        start = 0
        if cursor:
            try:
                decoded = base64.urlsafe_b64decode(cursor.encode("ascii")).decode()
                prefix, start_text = decoded.rsplit("/", 1)
                start = int(start_text)
                if prefix != revision_key or not 0 < start < len(items):
                    raise ValueError
            except (ValueError, UnicodeError):
                raise ServiceError(409, "CURSOR_EXPIRED", "评论已刷新，请从第一页开始。") from None
        end = start + limit
        next_cursor = base64.urlsafe_b64encode(f"{revision_key}/{end}".encode()).decode() if end < len(items) else None
        return Page(items=items[start:end], next_cursor=next_cursor, coverage=coverage, reason=reason)
