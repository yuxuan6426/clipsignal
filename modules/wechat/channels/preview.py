import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from uuid import NAMESPACE_URL, uuid5

import httpx

from .models import ServiceError, Video

ORIGIN = "https://channels.weixin.qq.com"
PREVIEW_PATH = "/finder-preview/api/feed/get_feed_info"
SHARE_PAGE = "/finder-preview/pages/sph"
SHORT_HOST = "weixin.qq.com"
SHORT_ID = re.compile(r"[A-Za-z0-9_-]{3,64}")


def canonical_share(url: str) -> str | None:
    """Identify the same work across the two public share URL formats."""
    parts = urlsplit(url)
    if parts.scheme != "https":
        return None
    if parts.netloc == SHORT_HOST and parts.path.startswith("/sph/"):
        key = parts.path.removeprefix("/sph/").removesuffix("/")
    elif parts.netloc == "channels.weixin.qq.com" and parts.path == SHARE_PAGE:
        keys = parse_qs(parts.query).get("id", [])
        key = keys[0] if len(keys) == 1 else ""
    else:
        return None
    if SHORT_ID.fullmatch(key):
        return f"https://{SHORT_HOST}/sph/{key}"
    return None


def read_public_preview(share_url: str) -> Video:
    key = share_url.rsplit("/", 1)[1]
    try:
        with httpx.Client(base_url=ORIGIN, timeout=5, trust_env=False) as client:
            response = client.post(
                PREVIEW_PATH,
                json={"baseReq": {"generalToken": ""}, "shortUri": key},
                headers={"Origin": ORIGIN, "Referer": f"{ORIGIN}{SHARE_PAGE}?id={key}"},
            )
            response.raise_for_status()
            raw = response.json()
            data = raw.get("data") or {}
            if raw.get("errCode") not in (0, "0") or data.get("errMsg", {}).get("type", 0) not in (0, "0"):
                raise ServiceError(404, "PREVIEW_UNAVAILABLE", "微信公开预览未提供此作品。")
            author = data["authorInfo"]
            feed = data["feedInfo"]
            nickname = author["nickname"]
            description = feed.get("description") or ""
            if not isinstance(nickname, str) or not nickname.strip() or not isinstance(description, str):
                raise ValueError("Invalid preview fields")
            published = datetime.fromtimestamp(int(feed["createtime"]), timezone.utc).isoformat()
    except httpx.TimeoutException:
        raise ServiceError(504, "PREVIEW_TIMEOUT", "微信公开预览请求超时，请稍后重试。") from None
    except httpx.HTTPStatusError as error:
        if error.response.status_code in {401, 403, 404, 410}:
            raise ServiceError(404, "PREVIEW_UNAVAILABLE", "微信公开预览未提供此作品。") from None
        raise ServiceError(502, "PREVIEW_FAILED", "微信公开预览暂时无法读取。") from None
    except (httpx.RequestError, AttributeError, KeyError, OverflowError, OSError, TypeError, ValueError):
        raise ServiceError(502, "PREVIEW_FAILED", "微信公开预览暂时无法读取。") from None

    def optional_text(value):
        return value if isinstance(value, str) and value else None

    video_id = uuid5(NAMESPACE_URL, share_url).hex
    return Video(
        id=video_id, creator_id="preview-" + video_id,
        title=next((line.strip()[:96] for line in description.splitlines() if line.strip()), "视频号作品"),
        description=description, author=nickname, share_url=share_url, published_display=published,
        observed_at=datetime.now(timezone.utc).isoformat(), source="wechat_public_preview",
        author_avatar_url=optional_text(author.get("headImgUrl")), cover_url=optional_text(feed.get("coverUrl")),
        comment_count_display=optional_text(feed.get("commentCountFmt")),
    )
