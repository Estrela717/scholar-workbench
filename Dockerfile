FROM node:22-slim AS frontend
WORKDIR /src
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY src ./src
COPY index.html vite.config.js ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY app ./app
COPY --from=frontend /src/dist ./dist
ENV PYTHONUNBUFFERED=1
EXPOSE 8765
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8765"]
