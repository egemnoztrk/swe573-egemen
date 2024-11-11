# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables to optimize Python runtime
ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1         

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (if any)
# For example, if you need gcc or other build tools, uncomment the following lines:
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that the Flask app runs on
EXPOSE 5000

# Define environment variables (optional defaults)
# You can override these at runtime using Docker environment variables
# ENV FLASK_SECRET_KEY=your_default_secret_key
# ENV MYSQL_URI=your_default_mysql_uri

# Command to run the application
CMD ["python", "app.py"]