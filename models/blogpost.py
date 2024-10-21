from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from bson import ObjectId


@dataclass
class BlogPost:
    title: str
    content: str
    author: str = "Anonymous"
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_published: bool = False
    photo_url: Optional[str] = None
    file_url: Optional[str] = None
    tags: list = field(default_factory=list)
    status: str = "NEW"
    comments: list = field(default_factory=list)
    _id: Optional[ObjectId] = None

    def to_dict(self):
        return {
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at,
            "is_published": self.is_published,
            "photo_url": self.photo_url,
            "file_url": self.file_url,
            "tags": self.tags,
            "status": self.status,
            "comments": self.comments,
            "_id": self._id
        }

    @staticmethod
    def from_dict(data):
        return BlogPost(
            title=data['title'],
            content=data['content'],
            author=data.get('author', 'Anonymous'),
            created_at=data.get('created_at', datetime.utcnow()),
            is_published=data.get('is_published', False),
            photo_url=data.get('photo_url'),
            file_url=data.get('file_url'),
            tags=data.get('tags', []),
            status=data.get('status', 'NEW'),
            comments=data.get('comments', []),
            _id=data.get('_id')
        )