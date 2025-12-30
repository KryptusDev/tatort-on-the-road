FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set python alias
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads output

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the API server
CMD ["python", "-m", "uvicorn", "app.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
