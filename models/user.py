from flask_sqlalchemy import SQLAlchemy
from models.db import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    age = db.Column(db.Integer, default=18)
    role = db.Column(db.String(20), default="user")

    def __init__(self, name, email, password_hash, age=18, role="user"):
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.age = age
        self.role = role

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "age": self.age,
            "role": self.role,
            "password_hash": self.password_hash
        }