FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including Node.js for email-service)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install Node dependencies for bundled email-service (faster startup)
RUN if [ -f "email-service/package.json" ]; then \
        if [ -f "email-service/package-lock.json" ]; then \
            npm --prefix email-service ci; \
        else \
            npm --prefix email-service install; \
        fi \
    fi

# Create uploads directory
RUN mkdir -p uploads

# Ensure start script is executable
RUN chmod +x start.sh

# Expose port (Render will set PORT environment variable)
# Default to 10000 to match Render's typical port
EXPOSE 10000

# Health check (using curl which is available in slim image)
# Use PORT env var or default to 10000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD sh -c 'curl -f http://localhost:${PORT:-10000}/health || exit 1'

# Run both services using the start script
CMD ["bash", "start.sh"]

