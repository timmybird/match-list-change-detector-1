FROM python:3.9-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install FOGIS API client from PyPI (version 0.5.3 with pipeline fixes)
RUN pip install --no-cache-dir fogis-api-client-timmyBird==0.5.3

# Install other dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .
COPY tests/ ./tests/

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_DIR=/app/logs

# Expose ports for metrics and health check
EXPOSE 8000

# Add health check for persistent service mode
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command supports both oneshot and service modes
# Set RUN_MODE=service environment variable to enable persistent service mode
CMD ["python", "persistent_service.py"]
