import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from threading import Lock

from .models import Comment, ServiceError

DATE = re.compile(r"^(?:昨天|今天|\d+(?:秒|分钟|小时|天)前|(?:\d{4}年)?\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2})(?:\s+\d{1,2}:\d{2})?$")
WORKER_LOCK = Lock()


def probe() -> tuple[str, str, str | None, list[Comment]]:
    try:
        with WORKER_LOCK:
            result = subprocess.run(
                [sys.executable, "-X", "utf8", "-m", "channels.uia_worker"],
                capture_output=True, timeout=24, encoding="utf-8", errors="replace",
                cwd=Path(__file__).resolve().parents[1],
                creationflags=subprocess.CREATE_NO_WINDOW, check=True,
            )
        payload = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ServiceError(503, "WECHAT_PROBE_FAILED", "微信读取超时或不可用，请重开独立窗口。") from error
    if payload["result"] != "ok":
        raise ServiceError(409, "CHANNELS_WINDOW_REQUIRED", "请在微信里打开一个独立的视频号窗口。")
    return parse_panel(payload["nodes"])


def parse_panel(nodes: list[dict]) -> tuple[str, str, str | None, list[Comment]]:
    children = defaultdict(list)
    for index, node in enumerate(nodes):
        children[node["parent"]].append(index)

    def label(index: int, role: str) -> str:
        node = nodes[index]
        return (node["name"] or "").strip() if node["role"] == role else ""

    def child_labels(index: int, role: str) -> list[str]:
        return [value for child in children[index] if (value := label(child, role))]

    for header, node in enumerate(nodes):
        if label(header, "Text") != "评论":
            continue
        peers = children[node["parent"]]
        tail = peers[peers.index(header) + 1:]
        marker = next((pos for pos, index in enumerate(tail[:12]) if label(index, "Text") == "作者"), None)
        if marker is not None and marker > 0:
            break
    else:
        raise ServiceError(409, "COMMENT_PANEL_REQUIRED", "请在独立窗口展开视频的评论面板，再读取。")

    names = child_labels(tail[marker - 1], "Text")
    if len(names) != 1 or not any(label(i, "Image") == names[0] for i in tail[:marker]):
        raise ServiceError(422, "WECHAT_LAYOUT_CHANGED", "评论面板的作者结构已变化。")
    tail = tail[marker + 1:]
    published = label(tail[0], "Text") if tail and DATE.fullmatch(label(tail[0], "Text")) else None
    if published:
        tail = tail[1:]
    description = label(tail[0], "Text") if tail else ""
    if not description:
        raise ServiceError(422, "VIDEO_DESCRIPTION_UNAVAILABLE", "此作品的说明未公开为可读取文本。")

    rows = []
    for position, (avatar, nickname) in enumerate(zip(tail, tail[1:])):
        images = child_labels(avatar, "Image")
        nicknames = child_labels(nickname, "Text")
        if len(nicknames) == 1 and nicknames[0] in images:
            rows.append((position, nicknames[0], "视频号" in child_labels(nickname, "Image")))

    result = []
    for number, (position, nickname, has_badge) in enumerate(rows):
        end = rows[number + 1][0] if number + 1 < len(rows) else len(tail)
        data = tail[position + 2:end]
        time_at = next((i for i, item in enumerate(data[:4]) if DATE.fullmatch(label(item, "Text"))), None)
        if time_at is None or time_at + 1 >= len(data):
            continue
        body = data[time_at + 1]
        text = label(body, "Text") or " ".join(child_labels(body, "Text"))
        if not text:
            continue
        controls = [label(item, "Button") for item in data[time_at + 2:]]
        likes = next((key.removeprefix("喜欢").lstrip(" ，,") for key in controls if key.startswith("喜欢")), None)
        replies = next((re.fullmatch(r"(?:展开\s*)?(\d+)\s*条回复", value) for value in controls
                        if re.fullmatch(r"(?:展开\s*)?\d+\s*条回复", value)), None)
        result.append(Comment(
            id=str(number + 1), author=nickname, text=text[:8000],
            time_display=label(data[time_at], "Text"), likes_display=likes or None,
            reply_count=int(replies.group(1)) if replies else None,
            profile_status="unverified" if has_badge else "no_visible_entry",
        ))
    counts = [label(i, "Text") for i in peers[peers.index(header) + 1:][:2]]
    if not result and "0" not in counts:
        raise ServiceError(422, "COMMENTS_UNAVAILABLE", "评论行尚未加载，或当前布局无法识别。")
    return names[0], description[:12000], published, result


if __name__ == "__main__":
    try:
        author, description, published, comments = probe()
        print(json.dumps({"status": "ok", "author": bool(author), "description": bool(description),
                          "publish_time": bool(published), "comments": len(comments)}))
    except ServiceError as error:
        print(json.dumps({"status": error.code}))
        raise SystemExit(1) from None
