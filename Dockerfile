FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for OpenCV with minimal size
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py logger.py rate_limiter.py ./

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MAX_WORKERS=4
ENV MAX_CONCURRENT_REQUESTS=6
ENV MAX_QUEUE_SIZE=500
ENV REQUEST_TIMEOUT=30

# Expose port
EXPOSE 8000

# Set proper signal handling
STOPSIGNAL SIGTERM

# Run the application
CMD ["python", "app.py"]
