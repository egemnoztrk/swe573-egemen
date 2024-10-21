from dataclasses import dataclass
from datetime import datetime
from bson import ObjectId
from flask import Flask, request, jsonify, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

import os
from werkzeug.utils import secure_filename

from models.blogpost import BlogPost
from models.user import User

# Configure upload folder and allowed file extensions
UPLOAD_FOLDER = './uploads'  # Path to store uploaded files locally
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx'}

class FlaskApp:
    def __init__(self, secret_key: str, mongo_uri: str, mongo_db_name: str):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.secret_key = secret_key
        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db_name
        self.mongo_client = self.connect_to_mongo()
        self.register_routes()

    def connect_to_mongo(self):
        mongo_client = MongoClient(self.mongo_uri)
        db_name = self.mongo_db_name
        self.db = mongo_client[db_name]
        print(f"Connected to MongoDB database: {db_name}")
        return mongo_client

    def register_routes(self):
        AuthRoutes(self.app, self.db) 
        BlogRoutes(self.app, self.db)

    def run(self):
        self.app.run()


class AuthRoutes:
    def __init__(self, app: Flask, db):
        self.app = app
        self.db = db
        self.initialize_routes()

    def initialize_routes(self):
        @self.app.route('/')
        def index():
            return jsonify({"message": "Welcome to the Flask App with MongoDB"})

        @self.app.route('/register', methods=['POST'])
        def register():
            data = request.json
            if not data or not data.get('email') or not data.get('password'):
                return jsonify({"error": "Email and password are required"}), 400

            existing_user = self.db['users'].find_one({"email": data['email']})
            if existing_user:
                return jsonify({"error": "User already exists"}), 400

            password_hash = generate_password_hash(data['password'])
            user = User(
                name=data.get('name'),
                email=data['email'],
                age=data.get('age', 18),
                password_hash=password_hash
            )

            self.db['users'].insert_one(user.to_dict())
            return jsonify({"message": "User registered successfully!"}), 201

        @self.app.route('/login', methods=['POST'])
        def login():
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400
            if not data.get('email') or not data.get('password'):
                return jsonify({"error": "Email and password are required"}), 400

            user = self.db['users'].find_one({"email": data['email']})
            if not user or not check_password_hash(user['password_hash'], data['password']):
                return jsonify({"error": "Invalid email or password"}), 401

            # Create session for the user
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']
            return jsonify({"message": f"Welcome {user['name']}!"}), 200

        @self.app.route('/logout', methods=['POST'])
        def logout():
            session.clear()
            return jsonify({"message": "Successfully logged out!"}), 200

        @self.app.route('/profile', methods=['GET'])
        def profile():
            if 'user_id' not in session:
                return jsonify({"error": "Unauthorized access!"}), 401

            user = self.db['users'].find_one({"_id": ObjectId(session['user_id'])})
            if user:
                user_data = {
                    "name": user['name'],
                    "email": user['email'],
                    "age": user['age'],
                    "role": user['role']
                }
                return jsonify(user_data), 200
            return jsonify({"error": "User not found!"}), 404

class BlogRoutes:
    def __init__(self, app: Flask, db):
        self.app = app
        self.app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        self.db = db
        self.initialize_routes()
        
    # Function to check allowed extensions
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def initialize_routes(self):
        @self.app.route('/blog/posts', methods=['POST'])
        def create_post():
            data = request.form
            files = request.files

            if not data or not data.get('title') or not data.get('content'):
                return jsonify({"error": "Title and content are required"}), 400

            photo_url = None
            if 'photo' in files and files['photo'].filename != '':
                photo = files['photo']
                filename = secure_filename(photo.filename) # type: ignore
                if self.allowed_file(photo.filename):
                    photo.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                    photo_url = f"/uploads/{filename}"

            file_url = None
            if 'file' in files and files['file'].filename != '':
                file = files['file']
                filename = secure_filename(file.filename) # type: ignore
                if self.allowed_file(file.filename):
                    file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                    file_url = f"/uploads/{filename}"

            tags = data.get('tags', "").split(",") if data.get('tags') else []
            status = data.get('status', "NEW")

            post = BlogPost(
                title=data['title'],
                content=data['content'],
                author=session.get('user_name', 'Anonymous'),
                is_published=bool(data.get('is_published', False)),
                photo_url=photo_url,
                file_url=file_url,
                tags=tags,
                status=status
            )

            self.db['blog_posts'].insert_one(post.to_dict())
            return jsonify({"message": "Post created successfully!"}), 201

        @self.app.route('/blog/post/status', methods=['PUT'])
        def update_status():
            """Update the status of a specific blog post (NEW or CLOSED)."""
            data = request.json
            if not data or 'post_id' not in data:
                return jsonify({"error": "Post ID is required"}), 400
            if 'status' not in data or data['status'] not in ['NEW', 'CLOSED']:
                return jsonify({"error": "Invalid or missing status"}), 400

            post = self.db['blog_posts'].find_one({"_id": ObjectId(data['post_id'])})
            if not post:
                return jsonify({"error": "Post not found"}), 404

            # Update the post's status
            self.db['blog_posts'].update_one({"_id": ObjectId(data['post_id'])}, {"$set": {"status": data['status']}})
            return jsonify({"message": "Post status updated successfully!"})

        @self.app.route('/blog/post/comments', methods=['POST'])
        def add_comment():
            """Add a comment to a specific blog post."""
            data = request.json
            if not data or not data.get('post_id') or not data.get('comment'):
                return jsonify({"error": "Post ID and Comment text are required"}), 400

            post = self.db['blog_posts'].find_one({"_id": ObjectId(data['post_id'])})
            if not post:
                return jsonify({"error": "Post not found"}), 404

            # Create comment data
            comment = {
                "author": session.get('user_name', 'Anonymous'),
                "comment": data['comment'],
                "created_at": datetime.utcnow()
            }

            # Append the comment to the comments array
            self.db['blog_posts'].update_one(
                {"_id": ObjectId(data['post_id'])},
                {"$push": {"comments": comment}}
            )

            return jsonify({"message": "Comment added successfully!"})

        @self.app.route('/blog/post', methods=['GET'])
        def get_post():
            """Retrieve a specific blog post by its ID."""
            post_id = request.args.get('post_id')
            if not post_id:
                return jsonify({"error": "Post ID is required"}), 400

            post = self.db['blog_posts'].find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"error": "Post not found"}), 404

            return jsonify({
                "_id": str(post["_id"]),
                "title": post["title"],
                "content": post["content"],
                "author": post["author"],
                "created_at": post["created_at"],
                "is_published": post["is_published"],
                "photo_url": post.get("photo_url"),
                "file_url": post.get("file_url"),
                "tags": post.get("tags", []),
                "status": post.get("status", "NEW"),
                "comments": post.get("comments", [])
            })

        @self.app.route('/blog/posts', methods=['GET'])
        def get_posts():
            """Retrieve all blog posts."""
            posts = self.db['blog_posts'].find()
            result = [{
                "_id": str(post["_id"]),
                "title": post["title"],
                "content": post["content"],
                "author": post["author"],
                "created_at": post["created_at"],
                "is_published": post["is_published"],
                "photo_url": post.get("photo_url"),
                "file_url": post.get("file_url"),
                "tags": post.get("tags", []),
                "status": post.get("status", "NEW"),
                "comments": post.get("comments", [])
            } for post in posts]
            return jsonify(result)

        @self.app.route('/blog/favorite', methods=['POST'])
        def favorite_post():
            """Favorite or unfavorite a blog post."""
            if 'user_id' not in session:
                return jsonify({"error": "Unauthorized access!"}), 401

            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400
            post_id = data.get('post_id')

            if not post_id:
                return jsonify({"error": "Post ID is required"}), 400

            user = self.db['users'].find_one({"_id": ObjectId(session['user_id'])})
            if not user:
                return jsonify({"error": "User not found!"}), 404

            # Check if the post exists
            post = self.db['blog_posts'].find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"error": "Post not found!"}), 404

            # Check if the post is already in the user's favorites
            if post_id in user.get('favorites', []):
                # Unfavorite the post
                self.db['users'].update_one(
                    {"_id": ObjectId(session['user_id'])},
                    {"$pull": {"favorites": post_id}}
                )
                return jsonify({"message": "Post unfavorited!"}), 200
            else:
                # Favorite the post
                self.db['users'].update_one(
                    {"_id": ObjectId(session['user_id'])},
                    {"$push": {"favorites": post_id}}
                )
                return jsonify({"message": "Post favorited!"}), 200

        @self.app.route('/user/favorites', methods=['GET'])
        def get_favorites():
            """Retrieve the list of user's favorited blog posts."""
            if 'user_id' not in session:
                return jsonify({"error": "Unauthorized access!"}), 401

            user = self.db['users'].find_one({"_id": ObjectId(session['user_id'])})
            if not user:
                return jsonify({"error": "User not found!"}), 404

            favorite_post_ids = user.get('favorites', [])
            favorite_posts = self.db['blog_posts'].find({"_id": {"$in": [ObjectId(post_id) for post_id in favorite_post_ids]}})

            result = [{
                "_id": str(post["_id"]),
                "title": post["title"],
                "content": post["content"],
                "author": post["author"],
                "created_at": post["created_at"],
                "is_published": post["is_published"],
                "photo_url": post.get("photo_url"),
                "file_url": post.get("file_url"),
                "tags": post.get("tags", []),
                "status": post.get("status", "NEW"),
                "comments": post.get("comments", [])
            } for post in favorite_posts]

            return jsonify(result)
        

        @self.app.route('/blog/unfavorite', methods=['POST'])
        def unfavorite_post():
            """Unfavorite a blog post."""
            if 'user_id' not in session:
                return jsonify({"error": "Unauthorized access!"}), 401

            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400
            post_id = data.get('post_id')

            if not post_id:
                return jsonify({"error": "Post ID is required"}), 400

            user = self.db['users'].find_one({"_id": ObjectId(session['user_id'])})
            if not user:
                return jsonify({"error": "User not found!"}), 404

            # Check if the post exists
            post = self.db['blog_posts'].find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"error": "Post not found!"}), 404

            # Check if the post is already in the user's favorites
            if post_id in user.get('favorites', []):
                # Unfavorite the post
                self.db['users'].update_one(
                    {"_id": ObjectId(session['user_id'])},
                    {"$pull": {"favorites": post_id}}
                )
                return jsonify({"message": "Post unfavorited!"}), 200
            else:
                return jsonify({"error": "Post not in favorites!"}), 400