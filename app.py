import os
from routes import FlaskApp

if __name__ == '__main__':
    # Initialize and run the Flask app
    flask_secret_key = os.getenv("FLASK_SECRET_KEY", "")
    mongo_uri = os.getenv("MONGO_URI", "")
    mongo_db_name = os.getenv("MONGO_DB_NAME", "")
    flask_app = FlaskApp(flask_secret_key, mongo_uri, mongo_db_name)
    flask_app.run()