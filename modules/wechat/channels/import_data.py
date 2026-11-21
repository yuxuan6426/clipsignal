import argparse
import sys
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints, ValidationError, model_validator

from .models import Coverage, ServiceError

Key = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]


class ImportRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportedProfile(ImportRecord):
    id: Key
    nickname: Key
    bio: str | None = None
    profile_url: str | None = None


class ImportedComment(ImportRecord):
    id: Key
    text: str
    author: Key
    account_id: Key | None = None
    time_display: str | None = None
    likes_display: str | None = None
    reply_count: int | None = None


class ImportedVideo(ImportRecord):
    id: Key
    title: Key
    description: str = ""
    author: Key
    account_id: Key | None = None
    share_url: str | None = None
    published_display: str | None = None
    comments_coverage: Coverage
    comments: list[ImportedComment]


class ImportBundle(ImportRecord):
    schema_version: Literal[1]
    source_id: Key
    source: Key
    exported_at: AwareDatetime
    profiles: list[ImportedProfile]
    videos: list[ImportedVideo]

    @model_validator(mode="after")
    def validate_references(self):
        accounts = {profile.id for profile in self.profiles}
        if len(accounts) != len(self.profiles) or len({video.id for video in self.videos}) != len(self.videos):
            raise ValueError("来源文件包含重复的账号或作品 ID。")
        for video in self.videos:
            if len({item.id for item in video.comments}) != len(video.comments):
                raise ValueError("同一作品包含重复的评论 ID。")
            if video.comments_coverage == "unavailable" and video.comments:
                raise ValueError("评论覆盖为 unavailable 时，评论列表应为空。")
            references = {item.account_id for item in video.comments} | {video.account_id}
            if references - accounts - {None}:
                raise ValueError("作品或评论引用了来源文件中缺失的账号。")
        return self


def main():
    from .server import DATA_DIR
    from .store import Store

    parser = argparse.ArgumentParser(description="导入有权使用的微信视频号记录。")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        bundle = ImportBundle.model_validate_json(args.file.read_text(encoding="utf-8-sig"))
        Store(DATA_DIR / "channels.sqlite3").import_bundle(bundle)
    except ValidationError as error:
        for issue in error.errors(include_url=False, include_input=False):
            location = ".".join(map(str, issue["loc"])) or "文件"
            print(f"{location}  {issue['msg']}", file=sys.stderr)
        raise SystemExit(2) from None
    except (OSError, UnicodeError, ServiceError) as error:
        raise SystemExit(str(error)) from None
    print(f"已导入 {len(bundle.videos)} 条作品和 {len(bundle.profiles)} 份主页资料。")


if __name__ == "__main__":
    main()
