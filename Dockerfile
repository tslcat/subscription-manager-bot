# 使用官方 Python 镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录下的文件复制到容器中的工作目录
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# ★★★ 关键修改：使用 python -m 方式启动（支持相对导入）★★★
CMD ["python", "-m", "app.main"]