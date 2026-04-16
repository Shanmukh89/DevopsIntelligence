FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc g++ libpq-dev git && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose the API port
EXPOSE 8000

# Copy the start script and make it executable
COPY start.sh .
RUN chmod +x start.sh

# Start FastAPI server AND Celery worker together!
CMD ["bash", "start.sh"]
