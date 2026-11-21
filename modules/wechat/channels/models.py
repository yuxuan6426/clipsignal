from typing import Literal

from pydantic import BaseModel, Field

PlaybackState = Literal["idle", "playing", "paused", "ended", "unavailable", "native_handoff"]
Coverage = Literal["partial", "complete", "unavailable"]
Source = Literal["wechat_uia", "test_fixture", "wechat_public_preview", "authorized_import", "socialdatax"]


class Video(BaseModel):
    id: str
    title: str
    description: str
    creator_id: str
    author: str
    published_display: str | None = None
    share_url: str | None = None
    observed_at: str
    source: Source = "wechat_uia"
    data_source: str | None = None
    author_avatar_url: str | None = None
    cover_url: str | None = None
    comment_count_display: str | None = None
    playback: Literal["wechat", "browser", "unavailable"] = "wechat"


class Comment(BaseModel):
    id: str
    author: str
    text: str
    time_display: str | None = None
    likes_display: str | None = None
    reply_count: int | None = None
    profile_status: Literal["unverified", "no_visible_entry", "linked"] = "unverified"
    creator_id: str | None = None


class Page(BaseModel):
    items: list[Comment]
    next_cursor: str | None
    coverage: Coverage
    reason: str | None = None
    source: Source | None = None
    video_id: str | None = None


class Creator(BaseModel):
    id: str
    nickname: str
    avatar_url: str | None = None
    profile_url: str | None = None
    profile_status: Literal["unverified", "linked"] = "unverified"
    bio: str | None = None
    source: Source | None = None
    data_source: str | None = None
    observed_at: str | None = None


class CreatorWorkLink(BaseModel):
    creator_id: str
    video_id: str
    title: str
    share_url: str
    source: Literal["authorized_import", "socialdatax"]


class Search(BaseModel):
    scope: Literal["local", "socialdatax"] = "local"
    items: list[Video]
    next_cursor: str | None = None


class Creators(BaseModel):
    scope: Literal["local"] = "local"
    items: list[Creator]


class Current(BaseModel):
    video: Video
    playback_state: PlaybackState


class Navigation(BaseModel):
    status: Literal["applied"]
    video_id: str


class ProfileNavigation(BaseModel):
    status: Literal["applied"]
    creator_id: str


class Capture(BaseModel):
    share_url: str | None = Field(default=None, max_length=2048)
    refresh_id: str | None = None


class ViewState(BaseModel):
    video_id: str | None = None
    playlist: list[str] = Field(default_factory=list, max_length=150)
    playback_state: PlaybackState = "idle"


class ServiceError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
