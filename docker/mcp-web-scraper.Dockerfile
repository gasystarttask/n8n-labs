FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    # Build tools for package compilation
    build-essential \
    # Port checking utility
    lsof \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY tools/mcp/mcp_web_scraper/requirements.txt /app/requirements.txt
COPY tools/mcp/mcp_core/requirements.txt /app/requirements-core.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-core.txt

# Copy MCP core and web scraper packages
COPY tools/mcp/mcp_core /app/mcp_core
COPY tools/mcp/mcp_web_scraper /app/mcp_web_scraper

# Install packages in editable mode
RUN cd /app/mcp_core && pip install -e . && \
    cd /app/mcp_web_scraper && pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8013

# Expose port
EXPOSE 8013

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
    CMD curl -f http://localhost:8013/health || exit 1

# Run the server
CMD ["python", "-m", "mcp_web_scraper.server", "--mode", "http"]
