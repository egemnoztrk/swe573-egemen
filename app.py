import time
from dotenv import load_dotenv
from routes import FlaskApp
import os

# Load environment variables at the module level
load_dotenv(override=True)
flask_secret_key = os.getenv("FLASK_SECRET_KEY", "")
mysql_uri = os.getenv("MYSQL_URI", "")

# Create the Flask app instance
flask_app = FlaskApp(flask_secret_key, mysql_uri)

if __name__ == '__main__':
    # Run the Flask development server
    flask_app.run()
    
    # Keep the process alive (optional)
    while True:
        time.sleep(60)