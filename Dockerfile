FROM python:3.11-slim

LABEL maintainer="B站动态监控系统"
LABEL description="B站UP主动态监控系统 - Web管理界面"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# 复制项目文件
COPY pyproject.toml README.md ./
COPY src/ src/

# 安装依赖
RUN pip install --no-cache-dir .

# 创建必要目录
RUN mkdir -p data logs images

# 使用 Docker 配置文件
RUN if [ -f configs/docker.yaml ]; then \
        cp configs/docker.yaml config.yaml; \
    fi

# 复制启动脚本
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

VOLUME ["/app/data", "/app/logs", "/app/images", "/app/config.yaml"]

CMD ["/app/start.sh"]
