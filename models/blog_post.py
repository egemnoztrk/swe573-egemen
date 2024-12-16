from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models.db import db

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False, default="Anonymous")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    photo_url = db.Column(db.String(255), nullable=True)
    file_url = db.Column(db.String(255), nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="NEW")
    attributes = db.Column(db.JSON, nullable=True)  # New optional field
    comments = db.relationship('Comment', backref='blog_post', lazy=True)

    def __init__(self, title, content, author="Anonymous", photo_url=None, file_url=None, 
                 tags=None, status="NEW", is_published=False, attributes=None):
        self.title = title
        self.content = content
        self.author = author
        self.photo_url = photo_url
        self.file_url = file_url
        self.tags = tags
        self.status = status
        self.is_published = is_published
        self.attributes = attributes  # Initialize the attributes field

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),  # Optional: format datetime
            "is_published": self.is_published,
            "photo_url": self.photo_url,
            "file_url": self.file_url,
            "tags": self.tags.split(",") if self.tags else [],
            "status": self.status,
            "attributes": self.attributes if self.attributes else {},  # Include attributes
            "comments": [comment.to_dict() for comment in self.comments]  # type: ignore
        }