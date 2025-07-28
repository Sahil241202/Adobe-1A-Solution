# Challenge 1A - PDF Outline Extractor Dockerfile
# Platform: linux/amd64, Offline, <200MB total size

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoclean

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create necessary directories with proper permissions
RUN mkdir -p /app/input /app/output /app/logs && \
    chown -R appuser:appuser /app

# Copy the application code
COPY --chown=appuser:appuser pdf_extractor/ ./pdf_extractor/
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser docker_entrypoint.py .
COPY --chown=appuser:appuser README.md .

# Set proper permissions
RUN chmod +x main.py docker_entrypoint.py && \
    chmod -R 755 /app/pdf_extractor

# Switch to non-root user
USER appuser

# Health check to verify the container is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import fitz; print('Container healthy')" || exit 1

# Expose volume mount points for documentation
VOLUME ["/app/input", "/app/output"]

# Container metadata
LABEL maintainer="Challenge 1A Solution"
LABEL description="PDF Outline Extractor for Adobe India Hackathon Challenge 1A"
LABEL version="1.0"
LABEL platform="linux/amd64"
LABEL challenge="1A"
LABEL requirements="CPU-only, <200MB, offline"

# Set default command to run the Docker entry point
CMD ["python", "docker_entrypoint.py"]
