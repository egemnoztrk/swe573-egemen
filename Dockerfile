# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port (e.g., 5000 for Flask)
EXPOSE 5000

# Run the Python app
CMD ["python", "app.py"]