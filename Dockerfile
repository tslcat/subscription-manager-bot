# 使用官方 Python 镜像（升级到 3.11，支持 str | None 语法）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将当前目录下的文件复制到容器
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# ====================== 【关键修复】设置北京时间 ======================
# 安装时区数据包并设置为 Asia/Shanghai
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 设置环境变量，让 Python 和系统都使用北京时间
ENV TZ=Asia/Shanghai
# =====================================================================

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 使用 python -m 方式启动（支持相对导入）← 保留你的改进
CMD ["python", "-m", "app.main"]