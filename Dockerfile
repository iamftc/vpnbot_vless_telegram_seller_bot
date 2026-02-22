# ═══════════════════════════════════════════════
# Multi-stage build for VPN Bot
# ═══════════════════════════════════════════════

# ── Stage 1: Dependencies ──────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ───────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Security: non-root user
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Copy dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY bot/ bot/
COPY alembic.ini .

# Switch to non-root
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["python", "-m", "bot.main"]
