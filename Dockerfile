# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY requirements.txt ./
# Cloud builds may supply their CA bundle. Render uses normal system trust.
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then PIP_CERT=/run/secrets/proxy_ca pip install --no-cache-dir -r requirements.txt; \
    else pip install --no-cache-dir -r requirements.txt; fi
RUN useradd --uid 10001 --create-home radar
COPY --chown=radar:radar src ./src
COPY --chown=radar:radar sql ./sql
USER radar
EXPOSE 8000
CMD ["python", "src/start.py", "web"]
