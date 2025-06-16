# Use Python base image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Copy files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Fly
EXPOSE 8080

# Run app with gunicorn on port 8080 (Fly expects this)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--timeout", "600"]

