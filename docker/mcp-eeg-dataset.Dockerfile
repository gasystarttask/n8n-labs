FROM python:3.11

# Install system dependencies (minimal for MongoDB client)
RUN apt-get update && apt-get install -y \
    build-essential \
    lsof \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY tools/mcp/mcp_eeg_dataset/requirements.txt /app/requirements.txt

# Install MCP server dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP core and eeg_dataset tool code
COPY tools/mcp/mcp_core /app/tools/mcp/mcp_core
COPY tools/mcp/mcp_eeg_dataset /app/tools/mcp/mcp_eeg_dataset

# Install MCP core and eeg_dataset as packages
RUN pip install --no-cache-dir /app/tools/mcp/mcp_core && \
    pip install --no-cache-dir /app/tools/mcp/mcp_eeg_dataset

# Set Python path
ENV PYTHONPATH=/app

# Create a non-root user that will be overridden by docker-compose
RUN useradd -m -u 1000 appuser

# Switch to non-root user
USER appuser

# Expose port (change if your server uses a different port)
EXPOSE 8012

# Run the MCP EEG Dataset server
CMD ["python", "-m", "mcp_eeg_dataset.server", "--mode", "http"]
