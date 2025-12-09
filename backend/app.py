#!/usr/bin/env python3
"""
Bot Factory + Task Manager - Unified Application
Combines bot code generation with scheduled task execution.
"""

import os
import sys
import re
import hmac
import yaml
import json
import sqlite3
import logging
import subprocess
import threading
import hashlib
import zipfile
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from contextlib import contextmanager
from functools import wraps

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Configuration
CONFIG_PATH = os.environ.get('CONFIG_PATH', '/app/config/tasks.yaml')
BOTS_PATH = os.environ.get('BOTS_PATH', '/app/bots')
DB_PATH = os.environ.get('DB_PATH', '/app/data/botfactory.db')
STATIC_PATH = os.environ.get('STATIC_PATH', '/app/frontend/dist')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '5000'))
AUTH_USER = os.environ.get('AUTH_USER', '')
AUTH_PASS = os.environ.get('AUTH_PASS', '')

# Logging Setup
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BotFactory')


# ==================================================
# Data Classes
# ==================================================

@dataclass
class TaskConfig:
    """Configuration for a scheduled task"""
    name: str
    script: str
    enabled: bool = True
    schedule: Optional[str] = None  # Cron expression
    interval: Optional[int] = None  # Seconds
    timeout: int = 300
    env: Dict[str, str] = None
    description: str = ""

    def __post_init__(self):
        if self.env is None:
            self.env = {}


# ==================================================
# Database
# ==================================================

class Database:
    """SQLite database for run history, logs, and bot configs"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript('''
                -- Task runs
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    exit_code INTEGER,
                    output TEXT,
                    error TEXT,
                    duration_seconds REAL
                );

                -- Task state
                CREATE TABLE IF NOT EXISTS task_state (
                    task_name TEXT PRIMARY KEY,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    last_run TEXT,
                    last_status TEXT,
                    run_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0
                );

                -- Saved bot configurations
                CREATE TABLE IF NOT EXISTS bot_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    config TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_runs_task ON runs(task_name);
                CREATE INDEX IF NOT EXISTS idx_runs_started ON runs(started_at);
            ''')

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # Run history methods
    def log_run_start(self, task_name: str) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO runs (task_name, started_at, status) VALUES (?, ?, ?)',
                (task_name, datetime.now().isoformat(), 'running')
            )
            return cursor.lastrowid

    def log_run_end(self, run_id: int, status: str, exit_code: int,
                    output: str, error: str, duration: float):
        with self._get_conn() as conn:
            conn.execute('''
                UPDATE runs
                SET finished_at = ?, status = ?, exit_code = ?,
                    output = ?, error = ?, duration_seconds = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), status, exit_code,
                  output[:50000] if output else None,
                  error[:50000] if error else None,
                  duration, run_id))

    def update_task_state(self, task_name: str, status: str):
        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO task_state (task_name, last_run, last_status, run_count, error_count, enabled)
                VALUES (?, ?, ?, 1, ?, 1)
                ON CONFLICT(task_name) DO UPDATE SET
                    last_run = excluded.last_run,
                    last_status = excluded.last_status,
                    run_count = run_count + 1,
                    error_count = error_count + CASE WHEN excluded.last_status = 'error' THEN 1 ELSE 0 END
            ''', (task_name, datetime.now().isoformat(), status,
                  1 if status == 'error' else 0))

    def get_task_state(self, task_name: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM task_state WHERE task_name = ?',
                (task_name,)
            ).fetchone()
            return dict(row) if row else None

    def set_task_enabled(self, task_name: str, enabled: bool):
        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO task_state (task_name, enabled)
                VALUES (?, ?)
                ON CONFLICT(task_name) DO UPDATE SET enabled = excluded.enabled
            ''', (task_name, 1 if enabled else 0))

    def get_recent_runs(self, limit: int = 50, task_name: str = None) -> List[Dict]:
        with self._get_conn() as conn:
            if task_name:
                rows = conn.execute('''
                    SELECT id, task_name, started_at, finished_at, status, exit_code, duration_seconds
                    FROM runs WHERE task_name = ?
                    ORDER BY started_at DESC LIMIT ?
                ''', (task_name, limit)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT id, task_name, started_at, finished_at, status, exit_code, duration_seconds
                    FROM runs ORDER BY started_at DESC LIMIT ?
                ''', (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_run_detail(self, run_id: int) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute('SELECT * FROM runs WHERE id = ?', (run_id,)).fetchone()
            return dict(row) if row else None

    def delete_run(self, run_id: int) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute('DELETE FROM runs WHERE id = ?', (run_id,))
            return cursor.rowcount > 0

    def clear_runs(self, task_name: str = None) -> int:
        with self._get_conn() as conn:
            if task_name:
                cursor = conn.execute('DELETE FROM runs WHERE task_name = ?', (task_name,))
            else:
                cursor = conn.execute('DELETE FROM runs')
            return cursor.rowcount

    def get_stats(self) -> Dict:
        with self._get_conn() as conn:
            total = conn.execute('SELECT COUNT(*) FROM runs').fetchone()[0]
            success = conn.execute(
                "SELECT COUNT(*) FROM runs WHERE status = 'success'"
            ).fetchone()[0]
            errors = conn.execute(
                "SELECT COUNT(*) FROM runs WHERE status = 'error'"
            ).fetchone()[0]
            today = conn.execute('''
                SELECT COUNT(*) FROM runs
                WHERE date(started_at) = date('now')
            ''').fetchone()[0]

            return {
                'total_runs': total,
                'successful_runs': success,
                'failed_runs': errors,
                'runs_today': today,
                'success_rate': round(success / total * 100, 1) if total > 0 else 0
            }

    # Bot config methods
    def save_bot_config(self, name: str, config: dict) -> int:
        with self._get_conn() as conn:
            now = datetime.now().isoformat()
            cursor = conn.execute('''
                INSERT INTO bot_configs (name, config, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    config = excluded.config,
                    updated_at = excluded.updated_at
            ''', (name, json.dumps(config), now, now))
            return cursor.lastrowid

    def get_bot_config(self, name: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM bot_configs WHERE name = ?', (name,)
            ).fetchone()
            if row:
                result = dict(row)
                result['config'] = json.loads(result['config'])
                return result
            return None

    def list_bot_configs(self) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                'SELECT id, name, created_at, updated_at FROM bot_configs ORDER BY updated_at DESC'
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_bot_config(self, name: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute('DELETE FROM bot_configs WHERE name = ?', (name,))
            return cursor.rowcount > 0


# ==================================================
# Task Runner
# ==================================================

class TaskRunner:
    """Executes Python scripts"""

    def __init__(self, db: Database, bots_path: str):
        self.db = db
        self.bots_path = bots_path
        self.running_tasks: Dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()

    def run_task(self, task: TaskConfig) -> Dict:
        """Execute a task and log the result"""
        script_path = os.path.join(self.bots_path, task.script)

        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            return {'status': 'error', 'error': f'Script not found: {task.script}'}

        with self._lock:
            if task.name in self.running_tasks:
                logger.warning(f"Task {task.name} is already running")
                return {'status': 'skipped', 'error': 'Task is already running'}

        run_id = self.db.log_run_start(task.name)
        start_time = datetime.now()

        logger.info(f"Starting task: {task.name} ({task.script})")

        try:
            env = os.environ.copy()
            env.update(task.env or {})
            env['TASK_NAME'] = task.name
            env['TASK_RUN_ID'] = str(run_id)

            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=os.path.dirname(script_path) or self.bots_path
            )

            with self._lock:
                self.running_tasks[task.name] = process

            try:
                stdout, stderr = process.communicate(timeout=task.timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                exit_code = -1
                stderr = f'Timeout after {task.timeout} seconds'.encode()

            duration = (datetime.now() - start_time).total_seconds()
            status = 'success' if exit_code == 0 else 'error'

            self.db.log_run_end(
                run_id, status, exit_code,
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace'),
                duration
            )
            self.db.update_task_state(task.name, status)

            logger.info(f"Task {task.name} finished: {status} (Exit: {exit_code}, Duration: {duration:.1f}s)")

            return {
                'status': status,
                'exit_code': exit_code,
                'duration': duration,
                'output': stdout.decode('utf-8', errors='replace')[-2000:],
                'error': stderr.decode('utf-8', errors='replace')[-2000:]
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.db.log_run_end(run_id, 'error', -1, '', str(e), duration)
            self.db.update_task_state(task.name, 'error')
            logger.exception(f"Error in task {task.name}")
            return {'status': 'error', 'error': str(e)}

        finally:
            with self._lock:
                self.running_tasks.pop(task.name, None)

    def is_running(self, task_name: str) -> bool:
        with self._lock:
            return task_name in self.running_tasks


# ==================================================
# Task Manager
# ==================================================

class TaskManager:
    """Main task manager with scheduling"""

    def __init__(self, config_path: str, bots_path: str, db: Database):
        self.config_path = config_path
        self.bots_path = bots_path
        self.db = db
        self.runner = TaskRunner(db, bots_path)
        self.scheduler = BackgroundScheduler()
        self.tasks: Dict[str, TaskConfig] = {}
        self._load_config()

    def _load_config(self):
        """Load task configuration from YAML"""
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found: {self.config_path}")
            return

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f) or {}

        for task_data in config.get('tasks', []):
            task = TaskConfig(**task_data)
            self.tasks[task.name] = task
            logger.info(f"Task loaded: {task.name}")

    def reload_config(self):
        """Reload configuration"""
        self.scheduler.remove_all_jobs()
        self.tasks.clear()
        self._load_config()
        self._schedule_tasks()
        logger.info("Configuration reloaded")

    def _schedule_tasks(self):
        """Schedule all enabled tasks"""
        for task in self.tasks.values():
            if not task.enabled:
                continue

            state = self.db.get_task_state(task.name)
            if state and not state.get('enabled', True):
                continue

            self._schedule_task(task)

    def _schedule_task(self, task: TaskConfig):
        """Schedule a single task"""
        job_id = f"task_{task.name}"

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        if task.schedule:
            trigger = CronTrigger.from_crontab(task.schedule)
            logger.info(f"Task {task.name} scheduled with cron: {task.schedule}")
        elif task.interval:
            trigger = IntervalTrigger(seconds=task.interval)
            logger.info(f"Task {task.name} scheduled every {task.interval}s")
        else:
            logger.warning(f"Task {task.name} has no schedule")
            return

        self.scheduler.add_job(
            self.runner.run_task,
            trigger=trigger,
            args=[task],
            id=job_id,
            name=task.name,
            replace_existing=True
        )

    def run_task_now(self, task_name: str) -> Dict:
        """Run a task immediately"""
        if task_name not in self.tasks:
            return {'status': 'error', 'error': 'Task not found'}

        task = self.tasks[task_name]

        result = {'status': 'pending'}
        def run():
            nonlocal result
            result = self.runner.run_task(task)

        thread = threading.Thread(target=run)
        thread.start()
        thread.join(timeout=1)

        if thread.is_alive():
            return {'status': 'started', 'message': 'Task started'}
        return result

    def enable_task(self, task_name: str, enabled: bool):
        """Enable or disable a task"""
        if task_name not in self.tasks:
            return False

        self.db.set_task_enabled(task_name, enabled)

        job_id = f"task_{task_name}"
        if enabled:
            self._schedule_task(self.tasks[task_name])
        else:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

        return True

    def get_status(self) -> Dict:
        """Get current status"""
        tasks_status = []
        for task in self.tasks.values():
            state = self.db.get_task_state(task.name) or {}
            job = self.scheduler.get_job(f"task_{task.name}")

            tasks_status.append({
                'name': task.name,
                'script': task.script,
                'description': task.description,
                'enabled': state.get('enabled', task.enabled),
                'schedule': task.schedule,
                'interval': task.interval,
                'running': self.runner.is_running(task.name),
                'last_run': state.get('last_run'),
                'last_status': state.get('last_status'),
                'run_count': state.get('run_count', 0),
                'error_count': state.get('error_count', 0),
                'next_run': job.next_run_time.isoformat() if job and job.next_run_time else None
            })

        return {
            'tasks': tasks_status,
            'stats': self.db.get_stats(),
            'scheduler_running': self.scheduler.running
        }

    def start(self):
        """Start the scheduler"""
        self._schedule_tasks()
        self.scheduler.start()
        logger.info("Task Manager started")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Task Manager stopped")


# ==================================================
# Bot Code Generator
# ==================================================

class BotGenerator:
    """Generates bot code from configuration"""

    @staticmethod
    def generate_dockerfile(config: dict) -> str:
        deps = ['requests', 'beautifulsoup4', 'feedparser', 'python-dateutil']

        ds = config.get('dataSources', {})
        proc = config.get('processing', {})
        out = config.get('outputs', {})
        sched = config.get('schedule', {})
        pro = config.get('professional', {})

        if ds.get('scraping', {}).get('enabled'):
            deps.extend(['lxml', 'cssselect'])
        if ds.get('api', {}).get('enabled'):
            deps.append('jsonpath-ng')

        if proc.get('aiRewrite'):
            provider = proc.get('aiProvider', 'anthropic')
            if provider == 'anthropic':
                deps.append('anthropic')
            elif provider == 'openai':
                deps.append('openai')
            elif provider == 'gemini':
                deps.append('google-generativeai')

        if out.get('matrix', {}).get('enabled'):
            deps.append('matrix-nio')

        if pro.get('healthCheck', {}).get('enabled') or pro.get('dashboard', {}).get('enabled'):
            deps.extend(['flask', 'flask-cors'])
        if pro.get('prometheus', {}).get('enabled'):
            deps.append('prometheus-client')
        if sched.get('type') == 'cron':
            deps.append('croniter')
        if pro.get('structuredLogging'):
            deps.append('python-json-logger')

        bot_name = config.get('botName', 'bot')
        dashboard_port = pro.get('dashboard', {}).get('port', 8080)
        tz = sched.get('timezone', 'Europe/Berlin')

        return f'''FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \\
    {' '.join(deps)}

COPY {bot_name}.py .
{"COPY templates/ ./templates/" if pro.get('dashboard', {}).get('enabled') else ""}

RUN mkdir -p /app/data
ENV TZ={tz}

{"EXPOSE " + str(dashboard_port) if pro.get('dashboard', {}).get('enabled') else ""}

{"HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:" + str(dashboard_port) + "/health || exit 1" if pro.get('healthCheck', {}).get('enabled') else ""}

CMD ["python", "-u", "{bot_name}.py"]
'''

    @staticmethod
    def generate_docker_compose(config: dict) -> str:
        bot_name = config.get('botName', 'bot')
        pro = config.get('professional', {})
        dashboard_port = pro.get('dashboard', {}).get('port', 8080)
        tz = config.get('schedule', {}).get('timezone', 'Europe/Berlin')

        compose = f'''services:
  {bot_name}:
    build: .
    container_name: {bot_name}
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    environment:
      - TZ={tz}'''

        if pro.get('dashboard', {}).get('enabled'):
            compose += f'''
    ports:
      - "{dashboard_port}:{dashboard_port}"'''

        return compose

    @staticmethod
    def generate_env_file(config: dict) -> str:
        ds = config.get('dataSources', {})
        proc = config.get('processing', {})
        out = config.get('outputs', {})
        sched = config.get('schedule', {})
        pro = config.get('professional', {})

        env = f'''# Bot Configuration
BOT_NAME={config.get('botName', 'bot')}
SEND_TIME={sched.get('time', '08:00')}
TZ={sched.get('timezone', 'Europe/Berlin')}
'''

        if proc.get('aiRewrite'):
            env += f"\nAI_PROVIDER={proc.get('aiProvider', 'anthropic')}\n"
            provider = proc.get('aiProvider')
            if provider == 'anthropic':
                env += f"ANTHROPIC_API_KEY={proc.get('aiApiKey', 'sk-ant-xxxxx')}\n"
            elif provider == 'openai':
                env += f"OPENAI_API_KEY={proc.get('aiApiKey', 'sk-xxxxx')}\n"
            elif provider == 'gemini':
                env += f"GOOGLE_API_KEY={proc.get('aiApiKey', 'AIzaxxxxx')}\n"
            elif provider == 'ollama':
                env += f"OLLAMA_URL={proc.get('ollamaUrl', 'http://localhost:11434')}\n"
                env += f"OLLAMA_MODEL={proc.get('ollamaModel', 'llama2')}\n"

        if ds.get('weather', {}).get('enabled'):
            env += f"\nOPENWEATHER_API_KEY={ds['weather'].get('apiKey', 'xxxxx')}\n"
            env += f"WEATHER_LOCATION={ds['weather'].get('location', 'Berlin,DE')}\n"

        if ds.get('homeassistant', {}).get('enabled'):
            ha = ds['homeassistant']
            env += f"\nHOMEASSISTANT_URL={ha.get('url', 'http://homeassistant.local:8123')}\n"
            env += f"HOMEASSISTANT_TOKEN={ha.get('token', '')}\n"

        if ds.get('zimaos', {}).get('enabled'):
            zima = ds['zimaos']
            env += f"\nZIMAOS_URL={zima.get('url', 'http://172.17.0.1')}\n"
            env += f"ZIMAOS_USER={zima.get('username', '')}\n"
            env += f"ZIMAOS_PASS={zima.get('password', '')}\n"

        if out.get('email', {}).get('enabled'):
            e = out['email']
            env += f'''
EMAIL_ENABLED=true
SMTP_SERVER={e.get('smtp', '')}
SMTP_PORT={e.get('port', 465)}
SMTP_USERNAME={e.get('user', '')}
SMTP_PASSWORD={e.get('pass', '')}
EMAIL_FROM={e.get('from', '')}
EMAIL_TO={e.get('to', '')}
'''

        if out.get('telegram', {}).get('enabled'):
            t = out['telegram']
            env += f'''
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN={t.get('botToken', '')}
TELEGRAM_CHAT_ID={t.get('chatId', '')}
'''

        if out.get('discord', {}).get('enabled'):
            env += f"\nDISCORD_ENABLED=true\nDISCORD_WEBHOOK_URL={out['discord'].get('webhookUrl', '')}\n"

        if out.get('slack', {}).get('enabled'):
            env += f"\nSLACK_ENABLED=true\nSLACK_WEBHOOK_URL={out['slack'].get('webhookUrl', '')}\n"

        if out.get('pushover', {}).get('enabled'):
            p = out['pushover']
            env += f'''
PUSHOVER_ENABLED=true
PUSHOVER_USER_KEY={p.get('userKey', '')}
PUSHOVER_API_TOKEN={p.get('apiToken', '')}
'''

        # Professional options
        env += f'''
# Professional Options
LOG_LEVEL={pro.get('logLevel', 'INFO')}
DASHBOARD_ENABLED={str(pro.get('dashboard', {}).get('enabled', True)).lower()}
DASHBOARD_PORT={pro.get('dashboard', {}).get('port', 8080)}
DASHBOARD_USERNAME={pro.get('dashboard', {}).get('username', 'admin')}
DASHBOARD_PASSWORD={pro.get('dashboard', {}).get('password', '')}
RETRY_ENABLED={str(pro.get('retry', {}).get('enabled', True)).lower()}
DRY_RUN={str(pro.get('dryRun', False)).lower()}
'''
        return env

    @staticmethod
    def generate_python_bot(config: dict) -> str:
        """Generate the main Python bot code with all features"""
        bot_name = config.get('botName', 'bot')
        description = config.get('botDescription', 'Generated bot')
        ds = config.get('dataSources', {})
        proc = config.get('processing', {})
        out = config.get('outputs', {})
        pro = config.get('professional', {})

        # Build imports
        imports = '''#!/usr/bin/env python3
"""
{bot_name} - Generated by Bot Factory
{description}
"""

import os
import sys
import json
import sqlite3
import hashlib
import logging
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
'''.format(bot_name=bot_name, description=description)

        if ds.get('rss', {}).get('enabled'):
            imports += "import feedparser\n"

        if ds.get('api', {}).get('enabled'):
            imports += "from jsonpath_ng import parse as jsonpath_parse\n"

        if proc.get('aiRewrite'):
            provider = proc.get('aiProvider', 'anthropic')
            if provider == 'anthropic':
                imports += "import anthropic\n"
            elif provider == 'openai':
                imports += "from openai import OpenAI\n"
            elif provider == 'gemini':
                imports += "import google.generativeai as genai\n"

        # Configuration section
        code = imports + '''
# ==================================================
# Configuration
# ==================================================

BOT_NAME = os.getenv('BOT_NAME', '{bot_name}')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
RETRY_ENABLED = os.getenv('RETRY_ENABLED', 'true').lower() == 'true'
RETRY_MAX = int(os.getenv('RETRY_MAX_ATTEMPTS', '3'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))

# Data directory
DATA_DIR = Path(os.getenv('DATA_DIR', '/app/data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / 'bot.db'

# Logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(BOT_NAME)

# ==================================================
# Database (Deduplication & History)
# ==================================================

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sent_items (
            id INTEGER PRIMARY KEY,
            item_hash TEXT UNIQUE,
            sent_at TEXT,
            item_type TEXT,
            title TEXT
        );
        CREATE TABLE IF NOT EXISTS run_history (
            id INTEGER PRIMARY KEY,
            started_at TEXT,
            finished_at TEXT,
            status TEXT,
            items_collected INTEGER,
            items_sent INTEGER,
            error TEXT
        );
    """)
    conn.commit()
    conn.close()

def is_already_sent(item_hash: str) -> bool:
    """Check if item was already sent"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT 1 FROM sent_items WHERE item_hash = ?", (item_hash,))
    result = cursor.fetchone() is not None
    conn.close()
    return result

def mark_as_sent(item_hash: str, item_type: str, title: str):
    """Mark item as sent"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO sent_items (item_hash, sent_at, item_type, title) VALUES (?, ?, ?, ?)",
        (item_hash, datetime.now().isoformat(), item_type, title[:200])
    )
    conn.commit()
    conn.close()

def log_run(started_at: str, status: str, items_collected: int, items_sent: int, error: str = None):
    """Log run to history"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO run_history (started_at, finished_at, status, items_collected, items_sent, error) VALUES (?, ?, ?, ?, ?, ?)",
        (started_at, datetime.now().isoformat(), status, items_collected, items_sent, error)
    )
    conn.commit()
    conn.close()

def get_item_hash(item: Dict) -> str:
    """Generate unique hash for an item"""
    content = json.dumps(item, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()

# ==================================================
# Retry Decorator
# ==================================================

def retry_on_error(max_retries: int = 3, backoff: float = 2.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not RETRY_ENABLED:
                return func(*args, **kwargs)
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    wait = backoff ** attempt
                    logger.warning(f"Attempt {{attempt + 1}} failed: {{e}}. Retrying in {{wait}}s...")
                    time.sleep(wait)
            raise last_error
        return wrapper
    return decorator

'''.format(bot_name=bot_name)

        # RSS Collection
        if ds.get('rss', {}).get('enabled'):
            feeds = ds['rss'].get('feeds', [])
            feeds_str = json.dumps(feeds)
            code += f'''
# ==================================================
# RSS Feed Collection
# ==================================================

RSS_FEEDS = {feeds_str}

@retry_on_error()
def collect_rss() -> List[Dict]:
    """Collect items from RSS feeds"""
    items = []
    for feed_config in RSS_FEEDS:
        try:
            logger.info(f"Fetching RSS: {{feed_config.get('name', feed_config.get('url'))}}")
            feed = feedparser.parse(feed_config['url'])
            for entry in feed.entries[:20]:  # Limit per feed
                item = {{
                    'type': 'rss',
                    'source': feed_config.get('name', 'RSS'),
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': BeautifulSoup(entry.get('summary', ''), 'html.parser').get_text()[:500],
                    'published': entry.get('published', ''),
                }}
                items.append(item)
        except Exception as e:
            logger.error(f"Error fetching RSS {{feed_config.get('url')}}: {{e}}")
    logger.info(f"Collected {{len(items)}} RSS items")
    return items

'''

        # REST API Collection
        if ds.get('api', {}).get('enabled'):
            endpoints = ds['api'].get('endpoints', [])
            endpoints_str = json.dumps(endpoints)
            code += f'''
# ==================================================
# REST API Collection
# ==================================================

API_ENDPOINTS = {endpoints_str}

@retry_on_error()
def collect_api() -> List[Dict]:
    """Collect data from REST APIs"""
    items = []
    for ep in API_ENDPOINTS:
        try:
            logger.info(f"Fetching API: {{ep.get('name', ep.get('url'))}}")
            headers = json.loads(ep.get('headers', '{{}}'))
            resp = requests.request(
                ep.get('method', 'GET'),
                ep['url'],
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()

            # Apply JSONPath if specified
            json_path = ep.get('jsonPath', '')
            if json_path:
                try:
                    expr = jsonpath_parse(json_path)
                    matches = [m.value for m in expr.find(data)]
                    data = matches[0] if len(matches) == 1 else matches
                except Exception as e:
                    logger.warning(f"JSONPath error: {{e}}")

            item = {{
                'type': 'api',
                'source': ep.get('name', 'API'),
                'title': ep.get('name', 'API Response'),
                'data': data,
                'url': ep['url'],
            }}
            items.append(item)
        except Exception as e:
            logger.error(f"Error fetching API {{ep.get('url')}}: {{e}}")
    logger.info(f"Collected {{len(items)}} API items")
    return items

'''

        # Web Scraping
        if ds.get('scraping', {}).get('enabled'):
            urls = ds['scraping'].get('urls', [])
            urls_str = json.dumps(urls)
            code += f'''
# ==================================================
# Web Scraping
# ==================================================

SCRAPE_URLS = {urls_str}

@retry_on_error()
def collect_scraping() -> List[Dict]:
    """Scrape data from websites"""
    items = []
    for url_config in SCRAPE_URLS:
        try:
            logger.info(f"Scraping: {{url_config.get('name', url_config.get('url'))}}")
            resp = requests.get(url_config['url'], timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            selector = url_config.get('selector', 'body')
            elements = soup.select(selector)

            for el in elements[:10]:
                item = {{
                    'type': 'scrape',
                    'source': url_config.get('name', 'Web'),
                    'title': url_config.get('name', 'Scraped'),
                    'content': el.get_text(strip=True)[:1000],
                    'url': url_config['url'],
                }}
                items.append(item)
        except Exception as e:
            logger.error(f"Error scraping {{url_config.get('url')}}: {{e}}")
    logger.info(f"Collected {{len(items)}} scraped items")
    return items

'''

        # Weather API
        if ds.get('weather', {}).get('enabled'):
            code += '''
# ==================================================
# Weather API
# ==================================================

WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
WEATHER_LOCATION = os.getenv('WEATHER_LOCATION', 'Berlin,DE')

@retry_on_error()
def collect_weather() -> List[Dict]:
    """Get weather data from OpenWeatherMap"""
    items = []
    if not WEATHER_API_KEY:
        logger.warning("No OpenWeatherMap API key configured")
        return items

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={WEATHER_LOCATION}&appid={WEATHER_API_KEY}&units=metric"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        weather = {
            'type': 'weather',
            'source': 'OpenWeatherMap',
            'title': f"Weather in {data.get('name', WEATHER_LOCATION)}",
            'temperature': data.get('main', {}).get('temp'),
            'feels_like': data.get('main', {}).get('feels_like'),
            'humidity': data.get('main', {}).get('humidity'),
            'description': data.get('weather', [{}])[0].get('description', ''),
            'wind_speed': data.get('wind', {}).get('speed'),
        }
        items.append(weather)
        logger.info(f"Weather: {weather['temperature']}°C, {weather['description']}")
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
    return items

'''

        # Home Assistant
        if ds.get('homeassistant', {}).get('enabled'):
            sensors = ds['homeassistant'].get('sensors', [])
            sensors_str = json.dumps(sensors)
            code += f'''
# ==================================================
# Home Assistant
# ==================================================

HA_URL = os.getenv('HOMEASSISTANT_URL', '')
HA_TOKEN = os.getenv('HOMEASSISTANT_TOKEN', '')
HA_SENSORS = {sensors_str}

@retry_on_error()
def collect_homeassistant() -> List[Dict]:
    """Get sensor data from Home Assistant"""
    items = []
    if not HA_URL or not HA_TOKEN:
        logger.warning("Home Assistant not configured")
        return items

    headers = {{"Authorization": f"Bearer {{HA_TOKEN}}", "Content-Type": "application/json"}}

    for sensor in HA_SENSORS:
        try:
            entity_id = sensor.get('entity', '')
            url = f"{{HA_URL}}/api/states/{{entity_id}}"
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            item = {{
                'type': 'homeassistant',
                'source': 'Home Assistant',
                'title': sensor.get('name', entity_id),
                'entity_id': entity_id,
                'state': data.get('state'),
                'unit': data.get('attributes', {{}}).get('unit_of_measurement', ''),
                'friendly_name': data.get('attributes', {{}}).get('friendly_name', ''),
            }}
            items.append(item)
            logger.info(f"HA {{entity_id}}: {{item['state']}} {{item['unit']}}")
        except Exception as e:
            logger.error(f"Error fetching HA sensor {{sensor}}: {{e}}")
    return items

'''

        # ZimaOS
        if ds.get('zimaos', {}).get('enabled'):
            metrics = ds['zimaos'].get('metrics', ['system', 'cpu', 'memory', 'apps'])
            metrics_str = json.dumps(metrics)
            code += f'''
# ==================================================
# ZimaOS API (with auto-login)
# ==================================================

ZIMAOS_URL = os.getenv('ZIMAOS_URL', '')
ZIMAOS_USER = os.getenv('ZIMAOS_USER', '')
ZIMAOS_PASS = os.getenv('ZIMAOS_PASS', '')
ZIMAOS_METRICS = {metrics_str}

_zimaos_token = None
_zimaos_token_time = None

def zimaos_login() -> str:
    """Login to ZimaOS and get access token"""
    global _zimaos_token, _zimaos_token_time
    from datetime import datetime, timedelta

    # Reuse token if less than 30 minutes old
    if _zimaos_token and _zimaos_token_time:
        if datetime.now() - _zimaos_token_time < timedelta(minutes=30):
            return _zimaos_token

    if not ZIMAOS_URL or not ZIMAOS_USER or not ZIMAOS_PASS:
        logger.warning("ZimaOS credentials not configured")
        return None

    try:
        resp = requests.post(
            f"{{ZIMAOS_URL}}/v1/users/login",
            json={{"username": ZIMAOS_USER, "password": ZIMAOS_PASS}},
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        # Token can be at data.token.access_token or data.access_token
        token_data = data.get('data', {{}})
        if isinstance(token_data, dict) and 'token' in token_data:
            _zimaos_token = token_data.get('token', {{}}).get('access_token')
        else:
            _zimaos_token = token_data.get('access_token') or data.get('access_token')
        if _zimaos_token:
            _zimaos_token_time = datetime.now()
            logger.info("ZimaOS login successful")
        else:
            logger.error(f"ZimaOS login response missing token. Response: {{data}}")
        return _zimaos_token
    except Exception as e:
        logger.error(f"ZimaOS login failed: {{e}}")
        return None

@retry_on_error()
def collect_zimaos() -> List[Dict]:
    """Collect system data from ZimaOS API"""
    items = []
    token = zimaos_login()
    if not token:
        return items

    headers = {{"Authorization": f"Bearer {{token}}"}}

    endpoints = {{
        'system': '/v2/zimaos/info',
        'cpu': '/v1/sys/utilization',
        'memory': '/v1/sys/utilization',
        'apps': '/v2/app_management/apps',
        'storage': '/v1/storage/disks',
    }}

    for metric in ZIMAOS_METRICS:
        if metric not in endpoints:
            continue
        try:
            url = f"{{ZIMAOS_URL}}{{endpoints[metric]}}"
            logger.info(f"Fetching ZimaOS {{metric}}: {{url}}")
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            # Extract relevant data based on metric type
            if metric == 'cpu':
                value = data.get('data', {{}}).get('cpu', data.get('cpu', {{}}))
                item = {{
                    'type': 'zimaos',
                    'source': 'ZimaOS',
                    'metric': 'cpu',
                    'title': 'CPU Usage',
                    'value': value.get('percent', value) if isinstance(value, dict) else value,
                    'data': value,
                }}
            elif metric == 'memory':
                value = data.get('data', {{}}).get('mem', data.get('mem', {{}}))
                item = {{
                    'type': 'zimaos',
                    'source': 'ZimaOS',
                    'metric': 'memory',
                    'title': 'Memory Usage',
                    'value': value.get('usedPercent', value) if isinstance(value, dict) else value,
                    'data': value,
                }}
            elif metric == 'system':
                item = {{
                    'type': 'zimaos',
                    'source': 'ZimaOS',
                    'metric': 'system',
                    'title': 'System Info',
                    'data': data.get('data', data),
                }}
            elif metric == 'apps':
                apps = data.get('data', data)
                if isinstance(apps, list):
                    item = {{
                        'type': 'zimaos',
                        'source': 'ZimaOS',
                        'metric': 'apps',
                        'title': f'Docker Apps ({{len(apps)}} running)',
                        'count': len(apps),
                        'apps': [a.get('name', 'unknown') for a in apps[:20]],
                    }}
                else:
                    item = {{'type': 'zimaos', 'source': 'ZimaOS', 'metric': 'apps', 'data': apps}}
            elif metric == 'storage':
                item = {{
                    'type': 'zimaos',
                    'source': 'ZimaOS',
                    'metric': 'storage',
                    'title': 'Storage Info',
                    'data': data.get('data', data),
                }}
            else:
                item = {{'type': 'zimaos', 'source': 'ZimaOS', 'metric': metric, 'data': data}}

            items.append(item)
            logger.info(f"ZimaOS {{metric}}: collected")
        except Exception as e:
            logger.error(f"Error fetching ZimaOS {{metric}}: {{e}}")

    logger.info(f"Collected {{len(items)}} ZimaOS items")
    return items

'''

        # AI Processing
        if proc.get('aiRewrite'):
            provider = proc.get('aiProvider', 'anthropic')
            if provider == 'anthropic':
                code += '''
# ==================================================
# AI Processing (Anthropic Claude)
# ==================================================

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

def process_with_ai(items: List[Dict]) -> List[Dict]:
    """Process items with Claude AI"""
    if not ANTHROPIC_API_KEY or not items:
        return items

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Build content summary
        content_parts = []
        for item in items[:10]:  # Limit items
            if item.get('title'):
                content_parts.append(f"- {item['title']}: {item.get('summary', item.get('content', ''))[:200]}")

        if not content_parts:
            return items

        prompt = f"""Summarize these items concisely in 2-3 paragraphs. Focus on the most important information:

{chr(10).join(content_parts)}

Provide a brief, informative summary."""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        summary = message.content[0].text
        logger.info("AI summary generated")

        return [{
            'type': 'ai_summary',
            'source': 'AI Summary',
            'title': 'Summary',
            'content': summary,
            'original_count': len(items)
        }]
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return items

'''
            elif provider == 'openai':
                code += '''
# ==================================================
# AI Processing (OpenAI)
# ==================================================

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

def process_with_ai(items: List[Dict]) -> List[Dict]:
    """Process items with OpenAI"""
    if not OPENAI_API_KEY or not items:
        return items

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        content_parts = []
        for item in items[:10]:
            if item.get('title'):
                content_parts.append(f"- {item['title']}: {item.get('summary', item.get('content', ''))[:200]}")

        if not content_parts:
            return items

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Summarize these items concisely:\\n\\n{chr(10).join(content_parts)}"
            }],
            max_tokens=1024
        )

        summary = response.choices[0].message.content
        logger.info("AI summary generated")

        return [{
            'type': 'ai_summary',
            'source': 'AI Summary',
            'title': 'Summary',
            'content': summary,
            'original_count': len(items)
        }]
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return items

'''
            elif provider == 'gemini':
                code += '''
# ==================================================
# AI Processing (Google Gemini)
# ==================================================

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

def process_with_ai(items: List[Dict]) -> List[Dict]:
    """Process items with Google Gemini"""
    if not GOOGLE_API_KEY or not items:
        return items

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        content_parts = []
        for item in items[:10]:
            if item.get('title'):
                content_parts.append(f"- {item['title']}: {item.get('summary', item.get('content', ''))[:200]}")

        if not content_parts:
            return items

        prompt = f"Summarize these items concisely in 2-3 paragraphs:\\n\\n{chr(10).join(content_parts)}"
        response = model.generate_content(prompt)

        summary = response.text
        logger.info("AI summary generated")

        return [{
            'type': 'ai_summary',
            'source': 'AI Summary',
            'title': 'Summary',
            'content': summary,
            'original_count': len(items)
        }]
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return items

'''
            elif provider == 'ollama':
                code += '''
# ==================================================
# AI Processing (Ollama - Local)
# ==================================================

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')

def process_with_ai(items: List[Dict]) -> List[Dict]:
    """Process items with local Ollama"""
    if not items:
        return items

    try:
        content_parts = []
        for item in items[:10]:
            if item.get('title'):
                content_parts.append(f"- {item['title']}: {item.get('summary', item.get('content', ''))[:200]}")

        if not content_parts:
            return items

        prompt = f"Summarize these items concisely in 2-3 paragraphs:\\n\\n{chr(10).join(content_parts)}"

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()

        summary = data.get('response', '')
        logger.info("AI summary generated (Ollama)")

        return [{
            'type': 'ai_summary',
            'source': 'AI Summary',
            'title': 'Summary',
            'content': summary,
            'original_count': len(items)
        }]
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return items

'''

        # Output: Telegram
        if out.get('telegram', {}).get('enabled'):
            code += '''
# ==================================================
# Output: Telegram
# ==================================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

def send_telegram(message: str) -> bool:
    """Send message via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message[:4000],
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        logger.info("Telegram message sent")
        return True
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

'''

        # Output: Discord
        if out.get('discord', {}).get('enabled'):
            code += '''
# ==================================================
# Output: Discord
# ==================================================

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

def send_discord(message: str) -> bool:
    """Send message via Discord webhook"""
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord not configured")
        return False

    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json={
            'content': message[:2000]
        }, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        logger.info("Discord message sent")
        return True
    except Exception as e:
        logger.error(f"Discord error: {e}")
        return False

'''

        # Output: Slack
        if out.get('slack', {}).get('enabled'):
            code += '''
# ==================================================
# Output: Slack
# ==================================================

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')

def send_slack(message: str) -> bool:
    """Send message via Slack webhook"""
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack not configured")
        return False

    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json={
            'text': message[:4000]
        }, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        logger.info("Slack message sent")
        return True
    except Exception as e:
        logger.error(f"Slack error: {e}")
        return False

'''

        # Output: Email
        if out.get('email', {}).get('enabled'):
            code += '''
# ==================================================
# Output: Email
# ==================================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = os.getenv('SMTP_SERVER', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USER = os.getenv('SMTP_USERNAME', '')
SMTP_PASS = os.getenv('SMTP_PASSWORD', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', '')
EMAIL_TO = os.getenv('EMAIL_TO', '')

def send_email(subject: str, body: str) -> bool:
    """Send email via SMTP"""
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO]):
        logger.warning("Email not fully configured")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO

        # Plain text
        msg.attach(MIMEText(body, 'plain'))

        # HTML version
        html = f"<html><body><pre>{body}</pre></body></html>"
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO.split(','), msg.as_string())

        logger.info("Email sent")
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False

'''

        # Output: Pushover
        if out.get('pushover', {}).get('enabled'):
            code += '''
# ==================================================
# Output: Pushover
# ==================================================

PUSHOVER_USER_KEY = os.getenv('PUSHOVER_USER_KEY', '')
PUSHOVER_API_TOKEN = os.getenv('PUSHOVER_API_TOKEN', '')

def send_pushover(message: str, title: str = None) -> bool:
    """Send message via Pushover"""
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        logger.warning("Pushover not configured")
        return False

    try:
        resp = requests.post("https://api.pushover.net/1/messages.json", data={
            'token': PUSHOVER_API_TOKEN,
            'user': PUSHOVER_USER_KEY,
            'message': message[:1024],
            'title': title or BOT_NAME,
        }, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        logger.info("Pushover message sent")
        return True
    except Exception as e:
        logger.error(f"Pushover error: {e}")
        return False

'''

        # Build collect_data function
        collectors = []
        if ds.get('rss', {}).get('enabled'):
            collectors.append('items.extend(collect_rss())')
        if ds.get('api', {}).get('enabled'):
            collectors.append('items.extend(collect_api())')
        if ds.get('scraping', {}).get('enabled'):
            collectors.append('items.extend(collect_scraping())')
        if ds.get('weather', {}).get('enabled'):
            collectors.append('items.extend(collect_weather())')
        if ds.get('homeassistant', {}).get('enabled'):
            collectors.append('items.extend(collect_homeassistant())')
        if ds.get('zimaos', {}).get('enabled'):
            collectors.append('items.extend(collect_zimaos())')

        collect_code = '\n    '.join(collectors) if collectors else '# No data sources configured'

        # Build send_outputs function
        outputs = []
        if out.get('telegram', {}).get('enabled'):
            outputs.append('send_telegram(message)')
        if out.get('discord', {}).get('enabled'):
            outputs.append('send_discord(message)')
        if out.get('slack', {}).get('enabled'):
            outputs.append('send_slack(message)')
        if out.get('email', {}).get('enabled'):
            outputs.append(f'send_email("{bot_name} Report", message)')
        if out.get('pushover', {}).get('enabled'):
            outputs.append('send_pushover(message)')

        send_code = '\n    '.join(outputs) if outputs else '# No outputs configured'

        # Deduplication
        dedup_enabled = proc.get('deduplication', True)

        # Main function
        code += f'''
# ==================================================
# Main Functions
# ==================================================

def collect_data() -> List[Dict]:
    """Collect data from all configured sources"""
    items = []
    {collect_code}
    return items

def format_message(items: List[Dict]) -> str:
    """Format items into a message"""
    lines = [f"📊 {{BOT_NAME}} Report", f"🕐 {{datetime.now().strftime('%Y-%m-%d %H:%M')}}", ""]

    for item in items:
        item_type = item.get('type', 'unknown')

        if item_type == 'ai_summary':
            lines.append(item.get('content', ''))
        elif item_type == 'weather':
            lines.append(f"🌡️ {{item.get('title')}}")
            lines.append(f"   {{item.get('temperature')}}°C (feels {{item.get('feels_like')}}°C)")
            lines.append(f"   {{item.get('description')}}, 💨 {{item.get('wind_speed')}} m/s")
        elif item_type == 'homeassistant':
            lines.append(f"🏠 {{item.get('title')}}: {{item.get('state')}} {{item.get('unit')}}")
        elif item_type == 'api':
            lines.append(f"📡 {{item.get('title')}}")
            data = item.get('data')
            if isinstance(data, dict):
                for k, v in list(data.items())[:5]:
                    lines.append(f"   {{k}}: {{v}}")
            else:
                lines.append(f"   {{str(data)[:200]}}")
        elif item_type == 'rss':
            lines.append(f"📰 {{item.get('title')}}")
            lines.append(f"   {{item.get('link')}}")
        elif item_type == 'scrape':
            lines.append(f"🔍 {{item.get('title')}}: {{item.get('content', '')[:100]}}")
        else:
            lines.append(f"• {{item.get('title', 'Item')}}")

        lines.append("")

    return "\\n".join(lines)

def send_outputs(message: str):
    """Send message to all configured outputs"""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would send message:\\n{{message[:500]}}...")
        return

    {send_code}

def main():
    """Main bot execution"""
    started_at = datetime.now().isoformat()
    logger.info(f"{{BOT_NAME}} starting...")

    init_db()
    items_sent = 0

    try:
        # Collect
        items = collect_data()
        logger.info(f"Collected {{len(items)}} items total")

        if not items:
            logger.info("No items collected, skipping")
            log_run(started_at, 'success', 0, 0)
            return 0

        # Deduplication
        {"new_items = []" if dedup_enabled else "new_items = items"}
        {"for item in items:" if dedup_enabled else ""}
        {"    item_hash = get_item_hash(item)" if dedup_enabled else ""}
        {"    if not is_already_sent(item_hash):" if dedup_enabled else ""}
        {"        new_items.append(item)" if dedup_enabled else ""}

        {"if not new_items:" if dedup_enabled else "if False:"}
            logger.info("No new items after deduplication")
            log_run(started_at, 'success', len(items), 0)
            return 0

        logger.info(f"{{len(new_items)}} new items after deduplication")

        # AI Processing
        {"processed = process_with_ai(new_items)" if proc.get('aiRewrite') else "processed = new_items"}

        # Format and send
        message = format_message(processed)
        send_outputs(message)

        # Mark as sent
        {"for item in new_items:" if dedup_enabled else ""}
        {"    mark_as_sent(get_item_hash(item), item.get('type', 'unknown'), item.get('title', ''))" if dedup_enabled else ""}

        items_sent = len(new_items)
        log_run(started_at, 'success', len(items), items_sent)
        logger.info(f"{{BOT_NAME}} completed successfully")
        return 0

    except Exception as e:
        logger.exception(f"{{BOT_NAME}} failed: {{e}}")
        log_run(started_at, 'error', 0, 0, str(e))
        return 1

if __name__ == '__main__':
    sys.exit(main())
'''

        return code


# ==================================================
# Flask Application
# ==================================================

app = Flask(__name__, static_folder=STATIC_PATH, static_url_path='')
CORS(app)

db: Optional[Database] = None
task_manager: Optional[TaskManager] = None


def check_auth():
    """Check Basic Auth if configured"""
    if not AUTH_USER or not AUTH_PASS:
        return True
    auth = request.authorization
    if not auth:
        return False
    # Use constant-time comparison to prevent timing attacks
    user_match = hmac.compare_digest(auth.username.encode(), AUTH_USER.encode())
    pass_match = hmac.compare_digest(auth.password.encode(), AUTH_PASS.encode())
    return user_match and pass_match


def require_auth(f):
    """Decorator for auth-protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_auth():
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Bot Factory"'
            })
        return f(*args, **kwargs)
    return decorated


def validate_bot_name(name: str) -> bool:
    """Validate bot name to prevent path traversal and injection"""
    if not name or len(name) > 50:
        return False
    # Only allow alphanumeric, dash, underscore, starting with letter
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_\-]*$', name))


# --------------------------------------------------
# Static Frontend
# --------------------------------------------------

@app.route('/')
def index():
    return send_from_directory(STATIC_PATH, 'index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(STATIC_PATH, 'bot.svg', mimetype='image/svg+xml')


@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(STATIC_PATH, 'assets'), path)


@app.route('/<path:path>')
def serve_static(path):
    # Security: Verify path is within STATIC_PATH to prevent traversal
    full_path = os.path.abspath(os.path.join(STATIC_PATH, path))
    if not full_path.startswith(os.path.abspath(STATIC_PATH)):
        return send_from_directory(STATIC_PATH, 'index.html')
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return send_from_directory(STATIC_PATH, path)
    return send_from_directory(STATIC_PATH, 'index.html')


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'scheduler_running': task_manager.scheduler.running if task_manager else False,
        'timestamp': datetime.now().isoformat()
    })


# --------------------------------------------------
# Task Manager API
# --------------------------------------------------

@app.route('/api/tasks/status')
@require_auth
def api_tasks_status():
    return jsonify(task_manager.get_status())


@app.route('/api/tasks/<task_name>/run', methods=['POST'])
@require_auth
def api_run_task(task_name):
    result = task_manager.run_task_now(task_name)
    return jsonify(result)


@app.route('/api/tasks/<task_name>/enable', methods=['POST'])
@require_auth
def api_enable_task(task_name):
    data = request.get_json() or {}
    enabled = data.get('enabled', True)
    if task_manager.enable_task(task_name, enabled):
        return jsonify({'status': 'ok', 'enabled': enabled})
    return jsonify({'status': 'error', 'error': 'Task not found'}), 404


@app.route('/api/tasks/reload', methods=['POST'])
@require_auth
def api_reload_tasks():
    task_manager.reload_config()
    return jsonify({'status': 'ok', 'message': 'Configuration reloaded'})


@app.route('/api/runs')
@require_auth
def api_runs():
    limit = request.args.get('limit', 50, type=int)
    task_name = request.args.get('task')
    runs = db.get_recent_runs(limit, task_name)
    return jsonify(runs)


@app.route('/api/runs/<int:run_id>')
@require_auth
def api_run_detail(run_id):
    run = db.get_run_detail(run_id)
    if run:
        return jsonify(run)
    return jsonify({'error': 'Run not found'}), 404


@app.route('/api/runs/<int:run_id>', methods=['DELETE'])
@require_auth
def api_delete_run(run_id):
    if db.delete_run(run_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Run not found'}), 404


@app.route('/api/runs', methods=['DELETE'])
@require_auth
def api_clear_runs():
    task_name = request.args.get('task')
    count = db.clear_runs(task_name)
    return jsonify({'success': True, 'deleted': count})


# --------------------------------------------------
# Bot Factory API
# --------------------------------------------------

@app.route('/api/bots', methods=['GET'])
@require_auth
def api_list_bots():
    """List saved bot configurations"""
    configs = db.list_bot_configs()
    return jsonify(configs)


@app.route('/api/bots', methods=['POST'])
@require_auth
def api_save_bot():
    """Save a bot configuration"""
    data = request.get_json()
    if not data or 'name' not in data or 'config' not in data:
        return jsonify({'error': 'Missing name or config'}), 400

    # Security: Validate bot name
    if not validate_bot_name(data['name']):
        return jsonify({'error': 'Invalid bot name. Use only letters, numbers, dash, underscore.'}), 400

    db.save_bot_config(data['name'], data['config'])
    return jsonify({'status': 'ok', 'message': 'Bot saved'})


@app.route('/api/bots/<name>', methods=['GET'])
@require_auth
def api_get_bot(name):
    """Get a saved bot configuration"""
    config = db.get_bot_config(name)
    if config:
        return jsonify(config)
    return jsonify({'error': 'Bot not found'}), 404


@app.route('/api/bots/<name>', methods=['DELETE'])
@require_auth
def api_delete_bot(name):
    """Delete a saved bot configuration"""
    if db.delete_bot_config(name):
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Bot not found'}), 404


@app.route('/api/tasks/<task_name>', methods=['DELETE'])
@require_auth
def api_delete_task(task_name):
    """Delete a deployed task completely (script + task entry + runs)"""
    if not validate_bot_name(task_name):
        return jsonify({'error': 'Invalid task name'}), 400

    deleted_items = []

    try:
        # 1. Remove from scheduler
        job_id = f"task_{task_name}"
        if task_manager.scheduler.get_job(job_id):
            task_manager.scheduler.remove_job(job_id)
            deleted_items.append('scheduler')

        # 2. Remove from tasks.yaml
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                tasks_config = yaml.safe_load(f) or {'tasks': []}

            original_count = len(tasks_config.get('tasks', []))
            tasks_config['tasks'] = [t for t in tasks_config.get('tasks', []) if t.get('name') != task_name]

            if len(tasks_config['tasks']) < original_count:
                with open(CONFIG_PATH, 'w') as f:
                    yaml.dump(tasks_config, f, default_flow_style=False)
                deleted_items.append('config')

        # 3. Delete script file
        script_path = os.path.join(BOTS_PATH, f'{task_name}.py')
        if os.path.exists(script_path):
            # Security: Verify path is within BOTS_PATH
            if os.path.abspath(script_path).startswith(os.path.abspath(BOTS_PATH)):
                os.remove(script_path)
                deleted_items.append('script')

        # 4. Clear run history for this task
        db.clear_runs(task_name)
        deleted_items.append('runs')

        # 5. Remove from task manager's in-memory tasks
        if task_name in task_manager.tasks:
            del task_manager.tasks[task_name]
            deleted_items.append('memory')

        if not deleted_items:
            return jsonify({'error': 'Task not found'}), 404

        logger.info(f"Deleted task {task_name}: {', '.join(deleted_items)}")
        return jsonify({
            'status': 'ok',
            'message': f'Task {task_name} deleted',
            'deleted': deleted_items
        })

    except Exception as e:
        logger.exception(f"Error deleting task {task_name}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bots/generate', methods=['POST'])
@require_auth
def api_generate_bot():
    """Generate bot code from configuration"""
    config = request.get_json()
    if not config:
        return jsonify({'error': 'Missing configuration'}), 400

    bot_name = config.get('botName', 'bot')
    if not validate_bot_name(bot_name):
        return jsonify({'error': 'Invalid bot name. Use only letters, numbers, dash, underscore.'}), 400

    try:
        files = {
            'Dockerfile': BotGenerator.generate_dockerfile(config),
            'docker-compose.yml': BotGenerator.generate_docker_compose(config),
            '.env': BotGenerator.generate_env_file(config),
            f"{config.get('botName', 'bot')}.py": BotGenerator.generate_python_bot(config)
        }
        return jsonify({'status': 'ok', 'files': files})
    except Exception as e:
        logger.exception("Error generating bot")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bots/download', methods=['POST'])
@require_auth
def api_download_bot():
    """Download bot as ZIP file"""
    config = request.get_json()
    if not config:
        return jsonify({'error': 'Missing configuration'}), 400

    try:
        bot_name = config.get('botName', 'bot')

        # Security: Validate bot name
        if not validate_bot_name(bot_name):
            return jsonify({'error': 'Invalid bot name. Use only letters, numbers, dash, underscore.'}), 400

        # Generate files
        files = {
            'Dockerfile': BotGenerator.generate_dockerfile(config),
            'docker-compose.yml': BotGenerator.generate_docker_compose(config),
            '.env': BotGenerator.generate_env_file(config),
            f'{bot_name}.py': BotGenerator.generate_python_bot(config)
        }

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                zf.writestr(f'{bot_name}/{filename}', content)

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{bot_name}.zip'
        )
    except Exception as e:
        logger.exception("Error creating ZIP")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bots/deploy', methods=['POST'])
@require_auth
def api_deploy_bot():
    """Deploy a bot to the bots directory"""
    config = request.get_json()
    if not config:
        return jsonify({'error': 'Missing configuration'}), 400

    try:
        bot_name = config.get('botName', 'bot')

        # Security: Validate bot name
        if not validate_bot_name(bot_name):
            return jsonify({'error': 'Invalid bot name. Use only letters, numbers, dash, underscore.'}), 400

        bot_path = os.path.join(BOTS_PATH, f'{bot_name}.py')

        # Security: Verify path is within BOTS_PATH
        if not os.path.abspath(bot_path).startswith(os.path.abspath(BOTS_PATH)):
            return jsonify({'error': 'Invalid bot path'}), 400

        # Generate and save the bot script
        code = BotGenerator.generate_python_bot(config)
        with open(bot_path, 'w') as f:
            f.write(code)

        # Add to tasks.yaml
        task_entry = {
            'name': bot_name,
            'script': f'{bot_name}.py',
            'description': config.get('botDescription', ''),
            'enabled': True
        }

        schedule = config.get('schedule', {})
        if schedule.get('type') == 'cron' and schedule.get('cron'):
            task_entry['schedule'] = schedule['cron']
        elif schedule.get('type') == 'interval':
            task_entry['interval'] = schedule.get('interval', 60) * 60
        elif schedule.get('type') == 'daily':
            time_parts = schedule.get('time', '08:00').split(':')
            task_entry['schedule'] = f"{time_parts[1] if len(time_parts) > 1 else '0'} {time_parts[0]} * * *"

        # Build environment variables for the task
        env_vars = {}
        ds = config.get('dataSources', {})
        proc = config.get('processing', {})
        out = config.get('outputs', {})

        # AI Provider
        if proc.get('aiEnabled'):
            env_vars['AI_PROVIDER'] = proc.get('aiProvider', 'anthropic')
            provider = proc.get('aiProvider', 'anthropic')
            if provider == 'anthropic':
                env_vars['ANTHROPIC_API_KEY'] = proc.get('aiApiKey', '')
            elif provider == 'openai':
                env_vars['OPENAI_API_KEY'] = proc.get('aiApiKey', '')
            elif provider == 'google':
                env_vars['GOOGLE_API_KEY'] = proc.get('aiApiKey', '')
            elif provider == 'ollama':
                env_vars['OLLAMA_URL'] = proc.get('ollamaUrl', 'http://localhost:11434')
                env_vars['OLLAMA_MODEL'] = proc.get('ollamaModel', 'llama2')

        # Data sources
        if ds.get('weather', {}).get('enabled'):
            env_vars['OPENWEATHER_API_KEY'] = ds['weather'].get('apiKey', '')
            env_vars['WEATHER_LOCATION'] = ds['weather'].get('location', 'Berlin,DE')

        if ds.get('homeassistant', {}).get('enabled'):
            ha = ds['homeassistant']
            env_vars['HOMEASSISTANT_URL'] = ha.get('url', '')
            env_vars['HOMEASSISTANT_TOKEN'] = ha.get('token', '')

        if ds.get('zimaos', {}).get('enabled'):
            zima = ds['zimaos']
            env_vars['ZIMAOS_URL'] = zima.get('url', 'http://172.17.0.1')
            env_vars['ZIMAOS_USER'] = zima.get('username', '')
            env_vars['ZIMAOS_PASS'] = zima.get('password', '')

        # Outputs
        if out.get('email', {}).get('enabled'):
            e = out['email']
            env_vars['EMAIL_ENABLED'] = 'true'
            env_vars['SMTP_SERVER'] = e.get('smtp', '')
            env_vars['SMTP_PORT'] = str(e.get('port', 465))
            env_vars['SMTP_USERNAME'] = e.get('user', '')
            env_vars['SMTP_PASSWORD'] = e.get('pass', '')
            env_vars['EMAIL_FROM'] = e.get('from', '')
            env_vars['EMAIL_TO'] = e.get('to', '')

        if out.get('telegram', {}).get('enabled'):
            t = out['telegram']
            env_vars['TELEGRAM_ENABLED'] = 'true'
            env_vars['TELEGRAM_BOT_TOKEN'] = t.get('botToken', '')
            env_vars['TELEGRAM_CHAT_ID'] = t.get('chatId', '')

        if out.get('discord', {}).get('enabled'):
            env_vars['DISCORD_ENABLED'] = 'true'
            env_vars['DISCORD_WEBHOOK_URL'] = out['discord'].get('webhookUrl', '')

        if out.get('slack', {}).get('enabled'):
            env_vars['SLACK_ENABLED'] = 'true'
            env_vars['SLACK_WEBHOOK_URL'] = out['slack'].get('webhookUrl', '')

        if out.get('pushover', {}).get('enabled'):
            p = out['pushover']
            env_vars['PUSHOVER_ENABLED'] = 'true'
            env_vars['PUSHOVER_USER_KEY'] = p.get('userKey', '')
            env_vars['PUSHOVER_API_TOKEN'] = p.get('apiToken', '')

        if env_vars:
            task_entry['env'] = env_vars

        # Update tasks.yaml
        tasks_file = CONFIG_PATH
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r') as f:
                tasks_config = yaml.safe_load(f) or {'tasks': []}
        else:
            tasks_config = {'tasks': []}

        # Update or add task
        existing = next((t for t in tasks_config['tasks'] if t['name'] == bot_name), None)
        if existing:
            existing.update(task_entry)
        else:
            tasks_config['tasks'].append(task_entry)

        with open(tasks_file, 'w') as f:
            yaml.dump(tasks_config, f, default_flow_style=False)

        # Reload task manager
        task_manager.reload_config()

        return jsonify({
            'status': 'ok',
            'message': f'Bot {bot_name} deployed and scheduled',
            'path': bot_path
        })

    except Exception as e:
        logger.exception("Error deploying bot")
        return jsonify({'error': str(e)}), 500


# --------------------------------------------------
# Files API (for viewing deployed bots)
# --------------------------------------------------

@app.route('/api/files/bots')
@require_auth
def api_list_bot_files():
    """List bot files in bots directory"""
    files = []
    if os.path.exists(BOTS_PATH):
        for f in os.listdir(BOTS_PATH):
            if f.endswith('.py'):
                path = os.path.join(BOTS_PATH, f)
                stat = os.stat(path)
                files.append({
                    'name': f,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    return jsonify(files)


@app.route('/api/files/bots/<filename>')
@require_auth
def api_get_bot_file(filename):
    """Get content of a bot file"""
    # Security: Validate filename to prevent path traversal
    if not filename.endswith('.py'):
        return jsonify({'error': 'Invalid file type'}), 400

    # Sanitize filename - only allow alphanumeric, dash, underscore
    if not re.match(r'^[\w\-]+\.py$', filename):
        return jsonify({'error': 'Invalid filename'}), 400

    # Resolve path and verify it's within BOTS_PATH
    path = os.path.abspath(os.path.join(BOTS_PATH, filename))
    if not path.startswith(os.path.abspath(BOTS_PATH)):
        return jsonify({'error': 'Invalid path'}), 400

    if not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404

    with open(path, 'r') as f:
        content = f.read()

    return jsonify({'name': filename, 'content': content})


# ==================================================
# Main Entry Point
# ==================================================

def main():
    global db, task_manager, STATIC_PATH

    import argparse
    parser = argparse.ArgumentParser(description='Bot Factory + Task Manager')
    parser.add_argument('--config', default=CONFIG_PATH, help='Tasks config file path')
    parser.add_argument('--bots', default=BOTS_PATH, help='Bots directory path')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    parser.add_argument('--static', default=STATIC_PATH, help='Static files path')
    parser.add_argument('--host', default=HOST, help='Server host')
    parser.add_argument('--port', type=int, default=PORT, help='Server port')
    parser.add_argument('--no-scheduler', action='store_true', help='Disable task scheduler')
    args = parser.parse_args()

    # Update STATIC_PATH from args (convert to absolute path)
    STATIC_PATH = os.path.abspath(args.static)
    app.static_folder = STATIC_PATH
    logger.info(f"Static files path: {STATIC_PATH}")

    # Create directories
    os.makedirs(args.bots, exist_ok=True)
    os.makedirs(os.path.dirname(args.db), exist_ok=True)
    os.makedirs(os.path.dirname(args.config), exist_ok=True)

    # Initialize database
    db = Database(args.db)

    # Initialize task manager
    task_manager = TaskManager(args.config, args.bots, db)

    if not args.no_scheduler:
        task_manager.start()

    try:
        logger.info(f"Bot Factory running at http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        if not args.no_scheduler:
            task_manager.stop()


if __name__ == '__main__':
    main()
