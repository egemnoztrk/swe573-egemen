from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models.db import db

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    blog_post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    author = db.Column(db.String(50), nullable=False, default="Anonymous")
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, blog_post_id, author, comment, created_at):
        self.blog_post_id = blog_post_id
        self.author = author
        self.comment = comment
        self.created_at = created_at

    def to_dict(self):
        return {
            "author": self.author,
            "comment": self.comment,
            "created_at": self.created_at
        }