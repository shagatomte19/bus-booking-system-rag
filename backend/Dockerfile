FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install PyTorch CPU version FIRST from PyTorch repository
RUN pip install --default-timeout=2000 --retries 10 --no-cache-dir \
    torch==2.7.1+cpu --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
RUN pip install --default-timeout=2000 --retries 10 --no-cache-dir -r requirements.txt


# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]