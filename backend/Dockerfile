FROM python:3.10-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Configure non-root user for Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    TEMP_DIR=/tmp/marino_processing

# Copy requirements and install dependencies in user space
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application source code and assets
COPY --chown=user:user app/ ./app/
COPY --chown=user:user assets/ ./assets/

# Ensure temp directory exists and is writable
USER root
RUN mkdir -p /tmp/marino_processing && chown -R user:user /tmp/marino_processing
USER user

# Expose default Hugging Face Spaces port
EXPOSE 7860

# Run FastAPI with Uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
