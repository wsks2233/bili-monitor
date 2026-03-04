# -*- coding: utf-8 -*-

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class StatInfo:
    like: int = 0
    repost: int = 0
    comment: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class VideoInfo:
    bvid: str = ""
    aid: int = 0
    title: str = ""
    description: str = ""
    duration: int = 0
    cover: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImageInfo:
    url: str = ""
    width: int = 0
    height: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DynamicInfo:
    dynamic_id: str
    uid: str
    upstream_name: str = ""
    dynamic_type: str = ""
    content: str = ""
    publish_time: datetime = None
    create_time: datetime = None
    images: List[ImageInfo] = field(default_factory=list)
    video: Optional[VideoInfo] = None
    stat: StatInfo = field(default_factory=StatInfo)
    raw_json: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.publish_time is None:
            self.publish_time = datetime.now()
        if self.create_time is None:
            self.create_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'dynamic_id': self.dynamic_id,
            'uid': self.uid,
            'upstream_name': self.upstream_name,
            'dynamic_type': self.dynamic_type,
            'content': self.content,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'images': [img.to_dict() for img in self.images],
            'video': self.video.to_dict() if self.video else None,
            'stat': self.stat.to_dict(),
        }
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class OpusParagraph:
    text: str = ""
    para_type: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OpusDetail:
    opus_id: str = ""
    title: str = ""
    content: str = ""
    paragraphs: List[OpusParagraph] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)
    author_name: str = ""
    author_uid: str = ""
    publish_time: datetime = None
    edit_time: datetime = None
    stat: StatInfo = field(default_factory=StatInfo)
    raw_json: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.publish_time is None:
            self.publish_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'opus_id': self.opus_id,
            'title': self.title,
            'content': self.content,
            'paragraphs': [p.to_dict() for p in self.paragraphs],
            'images': [img.to_dict() for img in self.images],
            'author_name': self.author_name,
            'author_uid': self.author_uid,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'edit_time': self.edit_time.isoformat() if self.edit_time else None,
            'stat': self.stat.to_dict(),
        }
        return result


@dataclass
class UpstreamInfo:
    uid: str
    name: str
    face: str = ""
    sign: str = ""
    level: int = 0
    fans: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
