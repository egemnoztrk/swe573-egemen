from dataclasses import dataclass
from datetime import datetime
import json
import traceback
from bson import ObjectId
from flask import Flask, request, jsonify, session, send_from_directory, make_response
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

            # Validate required fields
            if not data:
                return jsonify("No data provided"), 400
            if not data.get('title'):
                return jsonify("Title is required"), 400
            if not data.get('content'):
                return jsonify("Content is required"), 400
            if 'photo' not in files or files['photo'].filename == '':
                return jsonify("Photo is required"), 400
            if not data.get('tags'):
                return jsonify("Tags are required"), 400

            # Handle image upload (now storing in DB)
            photo_data = None
            photo_mimetype = None
            if 'photo' in files and files['photo'].filename != '':
                photo = files['photo']
                if self.allowed_file(photo.filename):
                    photo_data = photo.read()  # Read image content
                    photo_mimetype = photo.mimetype  # Store mimetype
                else:
                    return jsonify({"error": "File type not allowed"}), 400

            file_url = None
            if 'file' in files and files['file'].filename != '':
                file = files['file']
                if self.allowed_file(file.filename):
                    filename = secure_filename(file.filename) # type: ignore
                    file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                    file_url = f"/uploads/{filename}"

            # Handle attributes
            attributes = {}
            attributes_data = data.get('attributes')
            if attributes_data:
                try:
                    attributes = json.loads(attributes_data)
                    if not isinstance(attributes, dict):
                        return jsonify({"error": "Attributes must be a JSON object"}), 400
                except json.JSONDecodeError:
                    return jsonify({"error": "Invalid JSON format for attributes"}), 400

            # Process tags
            tags = data.get('tags', [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                    if not isinstance(tags, list):
                        raise ValueError("Parsed tags is not a list.")
                except (json.JSONDecodeError, ValueError):
                    tags = [tag.strip() for tag in tags.split(",") if tag.strip()] # type: ignore
            tags_list = [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()]
            tags_str = ",".join(tags_list) if tags_list else None

            # Create a new blog post instance with photo stored in DB
            post = BlogPost(
                title=data['title'],
                content=data['content'],
                author=session.get('user_name', 'Anonymous'),
                is_published=bool(int(data.get('is_published', 0))),
                file_url=file_url,
                tags=tags_str,
                status=data.get('status', "NEW"),
                attributes=attributes,
                photo=photo_data,
                photo_mimetype=photo_mimetype
            )

            try:
                db.session.add(post)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": "An error occurred while creating the post.", "details": str(e)}), 500

            return jsonify({"message": "Post created successfully!", "post_id": post.id}), 201

        @self.app.route('/blog/posts/<int:post_id>/photo', methods=['GET'])
        def get_post_photo(post_id):
            post = BlogPost.query.get(post_id)
            if not post or not post.photo:
                return jsonify({"error": "Photo not found"}), 404
            response = make_response(post.photo)
            response.headers.set('Content-Type', post.photo_mimetype or 'image/jpeg')
            return response

        @self.app.route('/blog/post/status', methods=['PUT'])
        def update_status():
            data = request.json
            if not data or 'post_id' not in data:
                return jsonify({"error": "Post ID is required"}), 400
            if 'status' not in data or data['status'] not in ['NEW', 'CLOSED']:
                return jsonify({"error": "Invalid or missing status"}), 400

            post = BlogPost.query.get(data['post_id'])
            if not post:
                return jsonify({"error": "Post not found"}), 404

            post.status = data['status']
            db.session.commit()
            return jsonify({"message": "Post status updated successfully!"})

        @self.app.route('/blog/post/comments', methods=['POST'])
        def add_comment():
            data = request.json
            if not data or not data.get('post_id') or not data.get('comment'):
                return jsonify({"error": "Post ID and Comment text are required"}), 400

            post = BlogPost.query.get(data['post_id'])
            if not post:
                return jsonify({"error": "Post not found"}), 404

            comment = Comment(
                blog_post_id=post.id,
                author=session.get('user_name', 'Anonymous'),
                comment=data['comment'],
                created_at=datetime.utcnow()
            )

            db.session.add(comment)
            db.session.commit()
            return jsonify({"message": "Comment added successfully!"})

        @self.app.route('/blog/post/comments', methods=['GET'])
        def get_comments():
            post_id = request.args.get('post_id')
            if not post_id:
                return jsonify({"error": "Post ID is required"}), 400

            post = BlogPost.query.get(post_id)
            if not post:
                return jsonify({"error": "Post not found"}), 404

            comments = Comment.query.filter_by(blog_post_id=post.id).all()
            result = [comment.to_dict() for comment in comments]
            result.reverse()
            return jsonify(result)

        @self.app.route('/blog/post', methods=['GET'])
        def get_post():
            post_id = request.args.get('post_id')
            if not post_id:
                return jsonify({"error": "Post ID is required"}), 400

            post = BlogPost.query.get(post_id)
            if not post:
                return jsonify({"error": "Post not found"}), 404

            return jsonify(post.to_dict())

        @self.app.route('/blog/posts', methods=['GET'])
        def get_posts():
            DEFAULT_LIMIT = 6
            MAX_LIMIT = 10

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
                result = [post.to_dict() for post in posts]
                return jsonify(result), 200
            except Exception as e:
                return jsonify({"error": "An error occurred while fetching posts."}), 500

        @self.app.route('/blog/posts/user', methods=['GET'])
        def get_user_posts():
            user_name = request.args.get('user_name') or session.get('user_name')
            if not user_name:
                return jsonify({"error": "User name is required"}), 400

            posts = BlogPost.query.filter_by(author=user_name).all()
            result = [post.to_dict() for post in posts]
            return jsonify(result), 200
        
        
        @self.app.route('/blog/search', methods=['GET'])
        def search_posts():
            query = request.args.get('query', '').strip()
            if not query:
                return jsonify({"error": "Query parameter is required"}), 400

            # Define a limit for the number of search results (optional)
            DEFAULT_LIMIT = 10
            try:
                limit = request.args.get('limit', default=DEFAULT_LIMIT, type=int)
                if limit < 1:
                    raise ValueError("Limit must be a positive integer.")
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400

            # Perform a case-insensitive search in title or content
            # You can add more fields as needed.
            matched_posts = BlogPost.query.filter(
                (BlogPost.title.ilike(f"%{query}%")) | # type: ignore
                (BlogPost.content.ilike(f"%{query}%")) # type: ignore
            ).order_by(BlogPost.created_at.desc()).limit(limit).all()

            results = [post.to_dict() for post in matched_posts]
            return jsonify(results), 200
