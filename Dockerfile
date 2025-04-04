FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY match_list_change_detector.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the script
CMD ["python", "match_list_change_detector.py"]
