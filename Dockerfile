FROM python:3.11-slim

LABEL maintainer="B站动态监控系统"
LABEL description="B站UP主动态监控系统 - Web管理界面"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir fastapi uvicorn python-multipart

COPY . .

RUN mkdir -p data logs images

# 使用 Docker 配置文件
RUN if [ -f config.docker.yaml ]; then \
        cp config.docker.yaml config.yaml; \
    fi

EXPOSE 8000

VOLUME ["/app/data", "/app/logs", "/app/images", "/app/config.yaml"]

CMD ["python", "web_main.py", "--host", "0.0.0.0", "--port", "8000"]
