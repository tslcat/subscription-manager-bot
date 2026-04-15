# 📅 Telegram 倒计时目标推送机器人

一个轻量、实用的个人 Telegram 机器人，帮助你管理重要目标和事件倒计时，每天自动推送剩余天数报告。

---

## ✨ 功能特点

- ✅ **添加目标**：支持任意名称 + 目标日期（格式：`YYYY-MM-DD`）
- ✅ **每日定时推送**：可自定义推送时间（默认 09:00）
- ✅ **智能高亮提醒**：今天、3天内自动加粗+紧急标记
- ✅ **内联按钮交互**：无需记住命令，一键操作
- ✅ **持久化存储**：使用 SQLite 数据库，数据永不丢失
- ✅ **Docker 一键部署**：支持 Docker / Docker Compose，部署简单稳定

---

## 🚀 部署（推荐使用 Docker）

### 前置要求

- 已安装 [Docker](https://www.docker.com/) 和 [Docker Compose](https://docs.docker.com/compose/)
- Telegram Bot Token（找 [@BotFather](https://t.me/botfather) 创建机器人获取）
- 你的 Telegram User ID（找 [@userinfobot](https://t.me/userinfobot) 发送任意消息获取）

---

### Docker安装

docker run -d \
  --name subscription-manager-bot \
  --restart unless-stopped \
  -v $(pwd)/data:/data \
  -e TG_BOT_TOKEN=**替换你的Telegram Bot Token** \
  -e TG_USER_ID=**替换你的Telegram ID**\
  tslcat/subscription-manager-bot:latestID

### Docker-Compose.yml安装

cat > docker-compose.yml << EOF
```
version: '3.8'

services:
  countdown-bot:
    build: .
    container_name: countdown-bot
    restart: unless-stopped
    volumes:
      - ./data:/data                  # 数据库持久化
    env_file:
      - .env
    environment:
      - TZ=\${TZ}
EOF
```
### 常用命令

docker compose logs -f          # 查看实时日志（按 Ctrl+C 退出）
docker compose restart          # 重启机器人
docker compose down             # 停止并删除容器
docker compose up -d --build    # 更新代码后重新构建启动
docker logs countdown-bot       # 查看最后一次日志

### 使用方法

添加目标
/addsub <目标名称> <目标日期>
示例：/addsub 考研 2026-12-20
查看所有目标
/subs

