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
    # Removed photo_url since we're storing images in the database
    photo = db.Column(db.LargeBinary, nullable=True)      # Storing the binary data of the image
    photo_mimetype = db.Column(db.String(50), nullable=True) # Mimetype of the stored image
    file_url = db.Column(db.String(255), nullable=True)    # Still storing file paths for non-image files (optional)
    tags = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="NEW")
    attributes = db.Column(db.JSON, nullable=True)
    comments = db.relationship('Comment', backref='blog_post', lazy=True)

    def __init__(self, title, content, author="Anonymous", file_url=None, 
                 tags=None, status="NEW", is_published=False, attributes=None, photo=None, photo_mimetype=None):
        self.title = title
        self.content = content
        self.author = author
        self.file_url = file_url
        self.tags = tags
        self.status = status
        self.is_published = is_published
        self.attributes = attributes
        self.photo = photo
        self.photo_mimetype = photo_mimetype

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "is_published": self.is_published,
            "file_url": self.file_url,
            "tags": self.tags.split(",") if self.tags else [],
            "status": self.status,
            "attributes": self.attributes if self.attributes else {},
            "photo_endpoint": f"/blog/posts/{self.id}/photo" if self.photo else None,
            "comments": [comment.to_dict() for comment in self.comments] # type: ignore
        }