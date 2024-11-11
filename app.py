import time
import os
from dotenv import load_dotenv
from routes import FlaskApp

if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv(override=True)

    # Retrieve environment variables
    flask_secret_key = os.getenv("FLASK_SECRET_KEY", "")
    mysql_uri = os.getenv("MYSQL_URI", "")
    
    # Initialize and run the Flask application
    flask_app = FlaskApp(flask_secret_key, mysql_uri)
    flask_app.run()
    
    # Keep the main thread alive
    while True:
        time.sleep(5)