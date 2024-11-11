import time
from dotenv import load_dotenv
from routes import FlaskApp
import os

if __name__ == '__main__':
    load_dotenv(override=True)
    
    flask_secret_key = os.getenv("FLASK_SECRET_KEY", "")
    mysql_uri = os.getenv("MYSQL_URI", "")
    flask_app = FlaskApp(flask_secret_key, mysql_uri)
    flask_app.run()
    
    while True:
        time.sleep(60)