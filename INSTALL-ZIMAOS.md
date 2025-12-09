# Bot Factory - ZimaOS Installation Guide

## Overview

Bot Factory is a web-based application for creating and managing automated Python bots. This guide explains how to install it on your ZimaOS device.

---

## Prerequisites

- ZimaOS device (ZimaCube, ZimaBoard, or similar)
- Docker and Docker Compose (pre-installed on ZimaOS)
- Web browser for accessing the dashboard

---

## Installation Methods

### Method 1: Docker Compose (Recommended)

1. **Connect to your ZimaOS via SSH**
   ```bash
   ssh root@<your-zimaos-ip>
   ```

2. **Create the application directory**
   ```bash
   mkdir -p /DATA/AppData/bot-factory
   cd /DATA/AppData/bot-factory
   ```

3. **Create the docker-compose.yml file**
   ```bash
   cat > docker-compose.yml << 'EOF'
   services:
     bot-factory:
       image: ghcr.io/chicohaager/bot-factory:latest
       container_name: bot-factory
       restart: unless-stopped
       ports:
         - "5050:5000"
       volumes:
         - ./data:/app/data
         - ./config:/app/config
         - ./bots:/app/bots
       environment:
         - TZ=Europe/Berlin
         - LOG_LEVEL=INFO
         # Optional: Enable authentication
         # - AUTH_USER=admin
         # - AUTH_PASS=your-secure-password
   EOF
   ```

4. **Create required directories**
   ```bash
   mkdir -p data config bots
   ```

5. **Create initial task configuration**
   ```bash
   cat > config/tasks.yaml << 'EOF'
   # Bot Factory Task Configuration
   # Add your scheduled bots here

   tasks: []
   EOF
   ```

6. **Start the application**
   ```bash
   docker compose up -d
   ```

7. **Access the dashboard**

   Open your browser and navigate to:
   ```
   http://<your-zimaos-ip>:5050
   ```

---

### Method 2: Build from Source

1. **Clone the repository**
   ```bash
   cd /DATA/AppData
   git clone https://github.com/chicohaager/bot-factory.git
   cd bot-factory/app
   ```

2. **Build and start**
   ```bash
   docker compose up -d --build
   ```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Web server port | `5000` |
| `TZ` | Timezone | `Europe/Berlin` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `AUTH_USER` | Basic auth username (optional) | - |
| `AUTH_PASS` | Basic auth password (optional) | - |
| `CONFIG_PATH` | Path to tasks.yaml | `/app/config/tasks.yaml` |
| `BOTS_PATH` | Path to bot scripts | `/app/bots` |
| `DB_PATH` | Path to SQLite database | `/app/data/botfactory.db` |

### Volume Mounts

| Container Path | Description |
|----------------|-------------|
| `/app/data` | Database and bot data storage |
| `/app/config` | Configuration files (tasks.yaml) |
| `/app/bots` | Generated and deployed bot scripts |

---

## Using Bot Factory

### Creating a Bot

1. Open the Bot Factory dashboard
2. Click on **Bot Factory** tab
3. Select a template or start from scratch
4. Configure:
   - **Data Sources**: RSS feeds, REST APIs, Web scraping, Weather, Home Assistant
   - **Processing**: Optional AI summarization
   - **Outputs**: Telegram, Discord, Slack, Email
   - **Schedule**: Daily, interval, or cron expression
5. Click **Generate** to create the bot
6. Click **Deploy to Task Manager** or **Download ZIP**

### Managing Tasks

1. Click on **Task Manager** tab
2. View all scheduled tasks
3. Use controls to:
   - Run a task manually
   - Enable/disable tasks
   - View run history and logs

---

## ZimaOS Integration

### Monitoring ZimaOS System

The **ZimaOS System Monitor** template is pre-configured with these endpoints:

| Endpoint | URL | Description |
|----------|-----|-------------|
| System Info | `http://localhost/v2/zimaos/info` | ZimaOS version and system info |
| CPU Usage | `http://localhost/v1/sys/utilization` | Current CPU utilization |
| Memory Usage | `http://localhost/v1/sys/utilization` | Current memory usage |
| Docker Apps | `http://localhost/v2/app_management/apps` | List of installed apps |

### Network Configuration

If running Bot Factory in Docker, use these URLs to access ZimaOS APIs:

```
http://host.docker.internal/v2/zimaos/info
```

Or use the ZimaOS gateway IP:
```
http://172.17.0.1/v2/zimaos/info
```

---

## Updating

### Update via Docker Compose

```bash
cd /DATA/AppData/bot-factory
docker compose pull
docker compose up -d
```

### Update from Source

```bash
cd /DATA/AppData/bot-factory
git pull
docker compose up -d --build
```

---

## Backup

### Backup Data

```bash
cd /DATA/AppData/bot-factory
tar -czvf bot-factory-backup-$(date +%Y%m%d).tar.gz data config bots
```

### Restore Data

```bash
cd /DATA/AppData/bot-factory
tar -xzvf bot-factory-backup-YYYYMMDD.tar.gz
docker compose restart
```

---

## Troubleshooting

### Check Logs

```bash
docker logs bot-factory -f
```

### Check Container Status

```bash
docker ps | grep bot-factory
```

### Restart the Application

```bash
cd /DATA/AppData/bot-factory
docker compose restart
```

### Reset Database

```bash
cd /DATA/AppData/bot-factory
rm data/botfactory.db
docker compose restart
```

### Port Conflicts

If port 5050 is already in use, change it in docker-compose.yml:
```yaml
ports:
  - "5051:5000"  # Change 5051 to any available port
```

---

## Uninstall

```bash
cd /DATA/AppData/bot-factory
docker compose down
cd /DATA/AppData
rm -rf bot-factory  # Warning: This deletes all data!
```

---

## Security Recommendations

1. **Enable Authentication**
   ```yaml
   environment:
     - AUTH_USER=admin
     - AUTH_PASS=your-secure-password
   ```

2. **Use HTTPS** (via ZimaOS reverse proxy or Nginx)

3. **Restrict Network Access** - Only expose to local network

4. **Regular Backups** - Automate backups of the data directory

---

## Support

- GitHub Issues: [Report bugs and feature requests]
- Documentation: [Full documentation]

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Restart | `docker compose restart` |
| Logs | `docker logs bot-factory -f` |
| Update | `docker compose pull && docker compose up -d` |
| Backup | `tar -czvf backup.tar.gz data config bots` |
