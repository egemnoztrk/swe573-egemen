import unittest
import json
from flask import Flask
from io import BytesIO

from routes import FlaskApp

class TestFlaskApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize the Flask app with test configuration
        secret_key = 'testsecret'
        # Use an in-memory SQLite database for testing
        mysql_uri = 'sqlite:///:memory:'
        cls.flask_app_instance = FlaskApp(secret_key, mysql_uri)
        cls.app = cls.flask_app_instance.app
        cls.app.testing = True
        cls.client = cls.app.test_client()

        # Create test database tables
        with cls.app.app_context():
            from models.db import db
            db.drop_all()  # Drop all tables, then re-create them
            db.create_all()

    def test_user_registration(self):
        """Test registering a new user with valid data"""
        payload = {
            "email": "testuser@example.com",
            "password": "securepassword",
            "name": "Test User"
        }
        response = self.client.post('/auth/register', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("User registered successfully!", response.get_data(as_text=True))

    def test_user_login(self):
        """Test logging in with a registered user"""
        # First register the user
        register_payload = {
            "email": "testlogin@example.com",
            "password": "loginpass",
            "name": "Login User"
        }
        self.client.post('/auth/register', json=register_payload)

        # Now login
        login_payload = {
            "email": "testlogin@example.com",
            "password": "loginpass"
        }
        response = self.client.post('/auth/login', json=login_payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome Login User!", response.get_data(as_text=True))
        
    def test_create_blog_post(self):
        """Test creating a blog post with a photo file"""
        # Register and login a user first
        self.client.post('/auth/register', json={
            "email": "poster@example.com",
            "password": "posterpass",
            "name": "Poster"
        })
        self.client.post('/auth/login', json={
            "email": "poster@example.com",
            "password": "posterpass"
        })

        data = {
            "title": "My Test Post",
            "content": "This is a test content.",
            "tags": json.dumps(["test", "blog"]),
            "is_published": "1"
        }

        data_file = {
            "photo": (BytesIO(b"fakeimagecontent"), "testimage.jpg")
        }

        response = self.client.post('/blog/posts', data=data|data_file, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 201)
        self.assertIn("Post created successfully!", response.get_data(as_text=True))
        
        # Capture the post_id for subsequent tests if needed
        resp_json = response.get_json()
        self.assertIn("post_id", resp_json)
        self.created_post_id = resp_json["post_id"]

    def test_get_single_post(self):
        """Test retrieving a single post by ID"""
        # First, create a post
        self.client.post('/auth/register', json={
            "email": "getter@example.com",
            "password": "getterpass",
            "name": "Getter"
        })
        self.client.post('/auth/login', json={
            "email": "getter@example.com",
            "password": "getterpass"
        })

        data = {
            "title": "Another Test Post",
            "content": "Testing retrieval.",
            "tags": json.dumps(["sample"]),
            "is_published": "1"
        }

        data_file = {
            "photo": (BytesIO(b"fakeimagecontent"), "anotherimage.jpg")
        }

        create_response = self.client.post('/blog/posts', data=data|data_file, content_type='multipart/form-data')
        self.assertEqual(create_response.status_code, 201)
        post_id = create_response.get_json()["post_id"]

        # Now retrieve that post
        get_response = self.client.get(f'/blog/post?post_id={post_id}')
        self.assertEqual(get_response.status_code, 200)
        post_data = get_response.get_json()
        self.assertEqual(post_data["id"], post_id)
        self.assertEqual(post_data["title"], "Another Test Post")

if __name__ == '__main__':
    unittest.main()