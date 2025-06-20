# Multi-stage build for optimal image size
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Production stage
FROM python:3.10-slim

# Create non-root user for security
RUN groupadd -r satellite && useradd -r -g satellite -s /bin/false satellite

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY requirements.txt .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R satellite:satellite /app

# Switch to non-root user
USER satellite

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MCP_SERVER_LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.satellite_calc import SatelliteCalculator; calc = SatelliteCalculator(); print('OK')" || exit 1

# Entry point  
ENTRYPOINT ["python", "-m", "src.mcp_server"]

# Default command
CMD []

# Labels for metadata
LABEL maintainer="Claude Code"
LABEL description="MCP Server for satellite orbital mechanics calculations"
LABEL version="1.0.0"