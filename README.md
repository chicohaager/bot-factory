# Bot Factory

A web-based application for creating and managing automated Python bots with a wizard interface.

## Screenshots

### Bot Factory - Template Selection
![Template Selection](screenshots/templates.png)

### Bot Factory - Data Sources
![Data Sources](screenshots/datasources.png)

### Task Manager
![Task Manager](screenshots/taskmanager.png)

## Features

- **Bot Generator**: Visual wizard to create Python automation bots
- **Task Manager**: Schedule and monitor bot executions
- **Multiple Data Sources**: RSS, REST API, Web Scraping, Weather, Home Assistant
- **AI Processing**: Anthropic, OpenAI, Google Gemini, Ollama integration
- **Output Channels**: Telegram, Discord, Slack, Email, Matrix
- **Professional Features**: Health checks, dashboards, metrics, retry logic

## Quick Start

### Docker (Recommended)

```bash
docker compose up -d
```

Access the dashboard at http://localhost:5000

### Manual Installation

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend (development)
cd frontend
npm install
npm run dev
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Web server port | `5000` |
| `TZ` | Timezone | `Europe/Berlin` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `AUTH_USER` | Basic auth username | - |
| `AUTH_PASS` | Basic auth password | - |

## Documentation

See [INSTALL-ZIMAOS.md](INSTALL-ZIMAOS.md) for ZimaOS installation instructions.

## Author

**Holger Kuehn**
Virtual Services
https://virtual-services.info

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## ☕ Support

If this project saves you time, you can buy me a coffee — it keeps the side projects going.

<!-- bmc-button -->
[![Buy Me A Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=%E2%98%95&slug=holgi18114&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://buymeacoffee.com/holgi18114)

… or scan the code:

<a href="https://buymeacoffee.com/holgi18114"><img src=".github/bmc-qr.png" alt="Buy Me a Coffee QR code" width="160"></a>
