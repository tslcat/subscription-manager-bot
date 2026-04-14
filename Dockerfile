FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录内容到容器中
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 启动命令
CMD ["python", "app/main.py"]