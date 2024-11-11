from dataclasses import dataclass
from datetime import datetime
import traceback
from bson import ObjectId
from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

import os
from werkzeug.utils import secure_filename

from models.blog_post import BlogPost
from models.user import User
from models.comment import Comment
from models.db import db

# Configure upload folder and allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx'}


class FlaskApp:
    def __init__(self, secret_key: str, mysql_uri: str):
        self.app = Flask(__name__, static_folder='static')
        self.app.config["SESSION_PERMANENT"] = True
        self.app.config["SESSION_TYPE"]      = "filesystem"
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mysql_uri
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.secret_key = secret_key
        self.app.config['UPLOAD_FOLDER'] = './uploads'
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
        self.register_routes()

    def register_routes(self):
        AuthRoutes(self.app)
        BlogRoutes(self.app)

        # Serve index.html on the root route
        @self.app.route('/')
        def serve_index():
            return send_from_directory(self.app.static_folder, 'index.html') # type: ignore
        
        @self.app.route('/login')
        def serve_login():
            return send_from_directory(self.app.static_folder, 'login.html') # type: ignore
        
        @self.app.route('/register')
        def serve_register():
            return send_from_directory(self.app.static_folder, 'register.html') # type: ignore
        
        @self.app.route('/profile')
        def serve_profile():
            return send_from_directory(self.app.static_folder, 'profile.html') # type: ignore
        
        @self.app.route('/post')
        def serve_post():
            return send_from_directory(self.app.static_folder, 'post.html') # type: ignore
                
        # New route to serve uploaded files
        @self.app.route('/uploads/<filename>')
        def uploaded_file(filename):
            # Serve the file from the configured upload folder
            return send_from_directory(self.app.config['UPLOAD_FOLDER'], filename)

    def run(self):
        try:
            self.app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5500)))
        except:
            self.app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5500)))


class AuthRoutes:
    def __init__(self, app: Flask):
        self.app = app
        self.initialize_routes()

    def initialize_routes(self):
        @self.app.route('/auth/register', methods=['POST'])
        def register():
            try:
                data = request.json
                if not data or not data.get('email') or not data.get('password'):
                    return jsonify({"error": "Email and password are required"}), 400

                # Check if the user already exists
                if User.query.filter_by(email=data['email']).first():
                    return jsonify({"error": "User already exists"}), 400

                # Hash the password and create a new user
                user = User(
                    name=data.get('name', 'Anonymous'),
                    email=data['email'],
                    password_hash=data['password'],
                    age=data.get('age', 18)
                )

                # Add the user to the session and commit
                db.session.add(user)
                db.session.commit()

                return jsonify({"message": "User registered successfully!"}), 201
            except:
                print(traceback.format_exc())
                return jsonify({"error": "An error occurred while registering the user"}), 500

        @self.app.route('/auth/login', methods=['POST'])
        def login():
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400
            if not data.get('email') or not data.get('password'):
                return jsonify({"error": "Email and password are required"}), 400

            # Find user by email
            user = User.query.filter_by(email=data['email']).first()
            if not user:
                return jsonify({"error": "Invalid email"}), 401
            if user.password_hash != data['password']:
                return jsonify({"error": "Invalid email or password"}), 401

            # Create a session for the user
            session['user_id'] = user.id
            session['user_name'] = user.name
            return jsonify({"message": f"Welcome {user.name}!"}), 200

        @self.app.route('/auth/logout', methods=['POST'])
        def logout():
            # Clear the session data
            session.clear()
            return jsonify({"message": "Successfully logged out!"}), 200

        @self.app.route('/auth/profile', methods=['GET'])
        def profile():
            # Check if the user is logged in
            if 'user_id' not in session:
                return jsonify({"error": "Unauthorized access!"}), 401

            # Retrieve the user data from the database
            user = User.query.get(session['user_id'])
            if user:
                user_data = {
                    "name": user.name,
                    "email": user.email,
                    "age": user.age,
                    "role": user.role
                }
                return jsonify(user_data), 200

            return jsonify({"error": "User not found!"}), 404
        
        @self.app.route('/auth/check_session', methods=['GET'])
        def check_session():
            if 'user_id' in session:
                return jsonify({"message": "Session active", "user_name": session['user_name']}), 200
            return jsonify({"error": "No active session"}), 401


class BlogRoutes:
    def __init__(self, app: Flask):
        self.app = app
        
        self.initialize_routes()

    # Helper method to check allowed file extensions
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def initialize_routes(self):
        @self.app.route('/blog/posts', methods=['POST'])
        def create_post():
            data = request.form
            files = request.files

            if not data or not data.get('title') or not data.get('content'):
                return jsonify({"error": "Title and content are required"}), 400

            # Handle file uploads
            photo_url = None
            if 'photo' in files and files['photo'].filename != '':
                photo = files['photo']
                if self.allowed_file(photo.filename):
                    filename = secure_filename(photo.filename) # type: ignore
                    photo.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                    photo_url = f"/uploads/{filename}"

            file_url = None
            if 'file' in files and files['file'].filename != '':
                file = files['file']
                if self.allowed_file(file.filename):
                    filename = secure_filename(file.filename) # type: ignore
                    file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                    file_url = f"/uploads/{filename}"

            # Create a new blog post instance
            post = BlogPost(
                title=data['title'],
                content=data['content'],
                author=session.get('user_name', 'Anonymous'),
                is_published=bool(data.get('is_published', False)),
                photo_url=photo_url,
                file_url=file_url,
                tags=",".join(data.get('tags', "").split(",")),
                status=data.get('status', "NEW")
            )

            db.session.add(post)
            db.session.commit()
            return jsonify({"message": "Post created successfully!"}), 201

        @self.app.route('/blog/post/status', methods=['PUT'])
        def update_status():
            data = request.json
            if not data or 'post_id' not in data:
                return jsonify({"error": "Post ID is required"}), 400
            if 'status' not in data or data['status'] not in ['NEW', 'CLOSED']:
                return jsonify({"error": "Invalid or missing status"}), 400

            # Find the post by ID
            post = BlogPost.query.get(data['post_id'])
            if not post:
                return jsonify({"error": "Post not found"}), 404

            # Update the post's status
            post.status = data['status']
            db.session.commit()
            return jsonify({"message": "Post status updated successfully!"})

        @self.app.route('/blog/post/comments', methods=['POST'])
        def add_comment():
            data = request.json
            if not data or not data.get('post_id') or not data.get('comment'):
                return jsonify({"error": "Post ID and Comment text are required"}), 400

            # Find the post by ID
            post = BlogPost.query.get(data['post_id'])
            if not post:
                return jsonify({"error": "Post not found"}), 404

            # Create a new comment instance
            comment = Comment(
                blog_post_id=post.id,
                author=session.get('user_name', 'Anonymous'),
                comment=data['comment'],
                created_at=datetime.utcnow()
            )

            db.session.add(comment)
            db.session.commit()
            return jsonify({"message": "Comment added successfully!"})

        @self.app.route('/blog/post', methods=['GET'])
        def get_post():
            post_id = request.args.get('post_id')
            if not post_id:
                return jsonify({"error": "Post ID is required"}), 400

            # Find the post by ID
            post = BlogPost.query.get(post_id)
            if not post:
                return jsonify({"error": "Post not found"}), 404

            return jsonify(post.to_dict())

        @self.app.route('/blog/posts', methods=['GET'])
        def get_posts():
            DEFAULT_LIMIT = 6
            MAX_LIMIT = 10  # Optional: to prevent excessive data retrieval

            try:
                limit = request.args.get('limit', default=DEFAULT_LIMIT, type=int)
                if limit < 1:
                    raise ValueError("Limit must be a positive integer.")
                if limit > MAX_LIMIT:
                    limit = MAX_LIMIT
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400

            try:
                posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(limit).all()                
                posts = list(reversed(posts))
                result = [post.to_dict() for post in posts]
                return jsonify(result), 200
            except Exception as e:
                # Log the exception as needed
                return jsonify({"error": "An error occurred while fetching posts."}), 500

        @self.app.route('/blog/posts/user', methods=['GET'])
        def get_user_posts():
            user_name = request.args.get('user_name') or session.get('user_name')
            if not user_name:
                return jsonify({"error": "User name is required"}), 400

            posts = BlogPost.query.filter_by(author=user_name).all()
            result = [post.to_dict() for post in posts]
            return jsonify(result), 200