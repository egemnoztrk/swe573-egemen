from dataclasses import dataclass, field
from datetime import datetime
from bson import ObjectId
from typing import Optional

@dataclass
class User:
    name: str
    email: str
    password_hash: str
    age: int = 18
    role: str = "user"
    favorites: list = field(default_factory=list)
    _id: Optional[ObjectId] = None

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "age": self.age,
            "role": self.role,
            "favorites": self.favorites,
            "_id": self._id
        }

    @staticmethod
    def from_dict(data):
        return User(
            name=data['name'],
            email=data['email'],
            password_hash=data['password_hash'],
            age=data.get('age', 18),
            role=data.get('role', 'user'),
            favorites=data.get('favorites', []),
            _id=data.get('_id')
        )