# ---- Build Stage ----
FROM python:3.14-slim AS builder

WORKDIR /app

# Install dependencies into a separate layer for caching
COPY Requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r Requirements.txt

# ---- Runtime Stage ----
FROM python:3.14-slim AS runtime

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Switch to non-root user
USER appuser

# Adjust this to your actual entry point (e.g. main.py, app.py)
CMD ["python", "main.py"]
