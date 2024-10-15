import os
from flask import Flask
from views import BasicRoutes

class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.secret_key = os.environ.get('SECRET_KEY')
        self.register_routes()

    def register_routes(self):
        BasicRoutes(self.app)  # Initialize the routes

    def run(self):
        self.app.run()

if __name__ == '__main__':
    flask_app = FlaskApp()
    flask_app.run()