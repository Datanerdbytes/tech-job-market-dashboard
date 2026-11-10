# Container deployment (Render / Railway / Cloud Run / any Docker host).
# Vercel deployments don't use this file — they use api/index.py + vercel.json.
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

ENV DASH_MCP=0
EXPOSE 8050
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--workers", "2", "--timeout", "120", "app:server"]
