# 使用官方 Python 镜像（升级到 3.11，支持 str | None 语法）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将当前目录下的文件复制到容器
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 使用 python -m 方式启动（支持相对导入）
CMD ["python", "-m", "app.main"]