# Use a specific Python version slim image
FROM python:3.12.1-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (optional, remove if not needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Create a non-root user and switch to it
RUN useradd -m appuser
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI with uvicorn (use --reload for development only)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
