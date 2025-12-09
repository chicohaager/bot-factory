import React, { useState, useEffect } from 'react';
import {
  Bot, Settings, Play, Clock, BarChart3, ChevronRight, ChevronLeft,
  Download, Copy, Check, Mail, Send, Globe, Database, Cpu, Zap,
  FileText, Eye, Home, MessageSquare, Hash, Server, Code,
  Activity, Shield, RefreshCw, AlertTriangle, Terminal, Layout,
  Plus, Trash2, Upload, Folder, Sun, Moon, Sparkles
} from 'lucide-react';

// ==================================================
// Templates
// ==================================================

const botTemplates = [
  {
    id: 'zimaos-monitor',
    name: 'ZimaOS System Monitor',
    icon: Server,
    desc: 'Monitors ZimaOS system status (CPU, RAM, Storage, Apps)',
    config: {
      botType: 'monitor',
      botName: 'zimaos-monitor',
      botDescription: 'Monitors ZimaOS system and sends status reports',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: { enabled: false, endpoints: [] },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] },
        zimaos: {
          enabled: true,
          url: 'http://172.17.0.1',
          username: '',
          password: '',
          metrics: ['system', 'cpu', 'memory', 'apps']
        }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: false },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: false, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'interval', time: '08:00', timezone: 'Europe/Berlin', interval: 60, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        prometheus: { enabled: true },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'energy-monitor',
    name: 'Energy Monitor',
    icon: Activity,
    desc: 'Power consumption & solar from Home Assistant',
    config: {
      botType: 'monitor',
      botName: 'energy-monitor',
      botDescription: 'Monitors energy consumption and sends daily reports',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: { enabled: false, endpoints: [] },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: true, location: 'Berlin,DE', apiKey: '' },
        homeassistant: {
          enabled: true,
          url: 'http://homeassistant.local:8123',
          token: '',
          sensors: [
            { entity: 'sensor.power_consumption', name: 'Power Consumption' },
            { entity: 'sensor.solar_power', name: 'Solar Production' }
          ]
        }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: false, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'daily', time: '20:00', timezone: 'Europe/Berlin', interval: 60, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'news-digest',
    name: 'News Digest',
    icon: FileText,
    desc: 'RSS feeds with AI summaries',
    config: {
      botType: 'newsletter',
      botName: 'news-digest',
      botDescription: 'Daily news digest from various sources',
      dataSources: {
        rss: { enabled: true, feeds: [{ name: 'Heise', url: 'https://www.heise.de/rss/heise.rdf' }] },
        api: { enabled: false, endpoints: [] },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: true, location: 'Berlin,DE', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: true, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: false, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'daily', time: '07:00', timezone: 'Europe/Berlin', interval: 60, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'price-tracker',
    name: 'Price Tracker',
    icon: Globe,
    desc: 'Monitor prices via web scraping',
    config: {
      botType: 'monitor',
      botName: 'price-tracker',
      botDescription: 'Monitors product prices and sends notifications',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: { enabled: false, endpoints: [] },
        scraping: { enabled: true, urls: [{ name: 'Product', url: '', selector: '.price' }] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: false, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'interval', time: '09:00', timezone: 'Europe/Berlin', interval: 30, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'api-monitor',
    name: 'API Monitor',
    icon: Server,
    desc: 'Monitor REST APIs and aggregate data',
    config: {
      botType: 'aggregator',
      botName: 'api-monitor',
      botDescription: 'Collects data from various APIs',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: { enabled: true, endpoints: [{ name: 'API 1', url: '', method: 'GET', headers: '{}', jsonPath: '' }] },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: false, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'interval', time: '08:00', timezone: 'Europe/Berlin', interval: 60, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'server-monitor',
    name: 'Server Monitor Bot',
    icon: Shield,
    desc: 'Uptime monitoring and health checks for HTTP endpoints',
    config: {
      botType: 'monitor',
      botName: 'server-monitor',
      botDescription: 'Monitors server uptime and health endpoints',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: {
          enabled: true,
          endpoints: [
            { name: 'Server Health', url: 'https://your-server.com/health', method: 'GET', headers: '{}', jsonPath: '' }
          ]
        },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: false },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: false, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'interval', time: '08:00', timezone: 'Europe/Berlin', interval: 5, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'weather-reporter',
    name: 'Weather Reporter Bot',
    icon: Sun,
    desc: 'Daily weather forecast and alerts',
    config: {
      botType: 'reporter',
      botName: 'weather-reporter',
      botDescription: 'Sends daily weather forecasts and severe weather alerts',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: { enabled: false, endpoints: [] },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: true, location: 'Berlin,DE', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: false },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: false, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'daily', time: '07:00', timezone: 'Europe/Berlin', interval: 60, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'news-alert',
    name: 'News Alert Bot',
    icon: AlertTriangle,
    desc: 'Instant notifications for keyword matches in RSS feeds',
    config: {
      botType: 'alert',
      botName: 'news-alert',
      botDescription: 'Monitors RSS feeds and sends alerts for keyword matches',
      dataSources: {
        rss: { enabled: true, feeds: [{ name: 'Tech News', url: 'https://news.ycombinator.com/rss' }] },
        api: { enabled: false, endpoints: [] },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: true, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'interval', time: '08:00', timezone: 'Europe/Berlin', interval: 15, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'backup-reporter',
    name: 'Backup Reporter Bot',
    icon: Database,
    desc: 'Reports on backup job status and disk space',
    config: {
      botType: 'reporter',
      botName: 'backup-reporter',
      botDescription: 'Monitors backup status and reports on disk space',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: {
          enabled: true,
          endpoints: [
            { name: 'Backup Status', url: 'http://your-backup-server/api/status', method: 'GET', headers: '{}', jsonPath: '' }
          ]
        },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: false },
      outputs: {
        email: { enabled: true, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: true, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'daily', time: '06:00', timezone: 'Europe/Berlin', interval: 60, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'la-palma-monitor',
    name: 'La Palma Monitor',
    icon: Activity,
    desc: 'News, weather, ship positions and volcanic activity for La Palma',
    config: {
      botType: 'aggregator',
      botName: 'la-palma-monitor',
      botDescription: 'Monitors La Palma news, weather, ships and volcanic activity',
      dataSources: {
        rss: { enabled: true, feeds: [{ name: 'La Palma News', url: 'https://lapalma1.net/feed/' }] },
        api: {
          enabled: true,
          endpoints: [
            { name: 'Volcanic Activity', url: 'https://api.example.com/volcano/lapalma', method: 'GET', headers: '{}', jsonPath: '' }
          ]
        },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: true, location: 'Santa Cruz de La Palma,ES', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: true, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: true, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: true, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'daily', time: '08:00', timezone: 'Europe/Berlin', interval: 60, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'social-aggregator',
    name: 'Social Aggregator Bot',
    icon: MessageSquare,
    desc: 'Aggregates content from multiple platforms',
    config: {
      botType: 'aggregator',
      botName: 'social-aggregator',
      botDescription: 'Collects and aggregates social media content',
      dataSources: {
        rss: {
          enabled: true,
          feeds: [
            { name: 'Twitter/X Feed', url: 'https://nitter.net/user/rss' },
            { name: 'Reddit', url: 'https://www.reddit.com/r/technology.rss' }
          ]
        },
        api: { enabled: false, endpoints: [] },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: true, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: true, botToken: '', chatId: '' },
        discord: { enabled: true, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'interval', time: '08:00', timezone: 'Europe/Berlin', interval: 30, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'event-reminder',
    name: 'Event Reminder Bot',
    icon: Clock,
    desc: 'Calendar-based event reminders',
    config: {
      botType: 'reminder',
      botName: 'event-reminder',
      botDescription: 'Sends reminders for upcoming calendar events',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: {
          enabled: true,
          endpoints: [
            { name: 'Calendar API', url: 'https://your-calendar-api.com/events', method: 'GET', headers: '{"Authorization": "Bearer TOKEN"}', jsonPath: '$.events' }
          ]
        },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: true, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'daily', time: '08:00', timezone: 'Europe/Berlin', interval: 60, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'ticket-alert',
    name: 'Ticket Alert Bot',
    icon: Zap,
    desc: 'Monitors ticket platforms and alerts on availability',
    config: {
      botType: 'alert',
      botName: 'ticket-alert',
      botDescription: 'Monitors ticket availability and sends instant alerts',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: { enabled: false, endpoints: [] },
        scraping: {
          enabled: true,
          urls: [
            { name: 'Ticket Site', url: 'https://ticket-site.com/event', selector: '.availability, .price' }
          ]
        },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: true },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: true, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'interval', time: '08:00', timezone: 'Europe/Berlin', interval: 5, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  },
  {
    id: 'uptime-monitor',
    name: 'Uptime Monitor',
    icon: Eye,
    desc: 'Monitor websites and services like Uptime Kuma',
    config: {
      botType: 'monitor',
      botName: 'uptime-monitor',
      botDescription: 'Monitors website and service uptime',
      dataSources: {
        rss: { enabled: false, feeds: [] },
        api: {
          enabled: true,
          endpoints: [
            { name: 'Uptime Kuma', url: 'http://uptime-kuma:3001/api/status-page/main', method: 'GET', headers: '{}', jsonPath: '' },
            { name: 'Website 1', url: 'https://your-website.com', method: 'GET', headers: '{}', jsonPath: '' }
          ]
        },
        scraping: { enabled: false, urls: [] },
        weather: { enabled: false, location: '', apiKey: '' },
        homeassistant: { enabled: false, url: '', token: '', sensors: [] }
      },
      processing: { aiRewrite: false, aiProvider: 'anthropic', aiApiKey: '', deduplication: false },
      outputs: {
        email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
        telegram: { enabled: false, botToken: '', chatId: '' },
        discord: { enabled: false, webhookUrl: '' },
        slack: { enabled: false, webhookUrl: '' },
        pushover: { enabled: false, userKey: '', apiToken: '' }
      },
      schedule: { type: 'interval', time: '08:00', timezone: 'Europe/Berlin', interval: 1, cron: '' },
      professional: {
        healthCheck: { enabled: true },
        dashboard: { enabled: true, port: 8080 },
        retry: { enabled: true, maxRetries: 3 },
        structuredLogging: true,
        logLevel: 'INFO',
        dryRun: false
      }
    }
  }
];

// ==================================================
// Theme Context
// ==================================================

const ThemeContext = React.createContext({ dark: false, toggle: () => {} });

function useTheme() {
  return React.useContext(ThemeContext);
}

// ==================================================
// Shared Components
// ==================================================

const Card = ({ children, className = '', selected, onClick }) => {
  const { dark } = useTheme();
  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-xl border-2 transition-all ${onClick ? 'cursor-pointer' : ''} ${
        selected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 shadow-lg'
          : dark
            ? 'border-gray-700 bg-gray-800 hover:border-gray-600'
            : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow'
      } ${className}`}
    >
      {children}
    </div>
  );
};

const Input = ({ label, value, onChange, placeholder, type = 'text', required, helpText }) => {
  const { dark } = useTheme();
  return (
    <div className="mb-4">
      <label className={`block text-sm font-medium mb-1 ${dark ? 'text-gray-300' : 'text-gray-700'}`}>
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
          dark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300'
        }`}
      />
      {helpText && <p className={`text-xs mt-1 ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{helpText}</p>}
    </div>
  );
};

const Toggle = ({ label, checked, onChange, description }) => {
  const { dark } = useTheme();
  return (
    <div className={`flex items-center justify-between py-3 border-b ${dark ? 'border-gray-700' : 'border-gray-100'}`}>
      <div>
        <span className={`font-medium ${dark ? 'text-gray-200' : 'text-gray-800'}`}>{label}</span>
        {description && <p className={`text-xs ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{description}</p>}
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative w-12 h-6 rounded-full transition-colors ${checked ? 'bg-blue-600' : dark ? 'bg-gray-600' : 'bg-gray-300'}`}
      >
        <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${checked ? 'translate-x-7' : 'translate-x-1'}`} />
      </button>
    </div>
  );
};

const StatusBadge = ({ status, running }) => {
  if (running) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
        Running
      </span>
    );
  }

  const styles = {
    success: 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300',
    error: 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300',
    idle: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
  };

  const s = status || 'idle';

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${styles[s] || styles.idle}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s === 'success' ? 'bg-green-500' : s === 'error' ? 'bg-red-500' : 'bg-gray-400'}`} />
      {s === 'success' ? 'Success' : s === 'error' ? 'Error' : 'Ready'}
    </span>
  );
};

// ==================================================
// Task Manager Component
// ==================================================

function TaskManager() {
  const { dark } = useTheme();
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({});
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/tasks/status');
      const data = await res.json();
      setTasks(data.tasks || []);
      setStats(data.stats || {});
    } catch (e) {
      console.error('Error fetching status:', e);
    }
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch('/api/runs?limit=20');
      const data = await res.json();
      setRuns(data);
    } catch (e) {
      console.error('Error fetching runs:', e);
    }
  };

  useEffect(() => {
    Promise.all([fetchStatus(), fetchRuns()]).then(() => setLoading(false));
    const interval = setInterval(() => {
      fetchStatus();
      fetchRuns();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const runTask = async (taskName) => {
    await fetch(`/api/tasks/${taskName}/run`, { method: 'POST' });
    setTimeout(fetchStatus, 500);
    setTimeout(fetchRuns, 1000);
  };

  const toggleTask = async (taskName, enabled) => {
    await fetch(`/api/tasks/${taskName}/enable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });
    fetchStatus();
  };

  const deleteTask = async (taskName) => {
    if (!confirm(`Are you sure you want to permanently delete the bot "${taskName}"?\n\nThis will remove:\n- The bot script\n- The scheduled task\n- All run history`)) return;
    try {
      const res = await fetch(`/api/tasks/${taskName}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.status === 'ok') {
        fetchStatus();
        fetchRuns();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (e) {
      alert(`Error: ${e.message}`);
    }
  };

  const reloadConfig = async () => {
    await fetch('/api/tasks/reload', { method: 'POST' });
    fetchStatus();
  };

  const viewRunDetail = async (runId) => {
    const res = await fetch(`/api/runs/${runId}`);
    setSelectedRun(await res.json());
  };

  const deleteRun = async (runId) => {
    if (!confirm('Are you sure you want to delete this run?')) return;
    await fetch(`/api/runs/${runId}`, { method: 'DELETE' });
    fetchStatus();
  };

  const formatDate = (iso) => {
    if (!iso) return '-';
    return new Date(iso).toLocaleString('en-GB', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <div className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Active Tasks</div>
          <div className="text-2xl font-bold text-blue-600">{tasks.filter(t => t.enabled).length}</div>
        </Card>
        <Card>
          <div className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Runs Today</div>
          <div className={`text-2xl font-bold ${dark ? 'text-white' : ''}`}>{stats.runs_today || 0}</div>
        </Card>
        <Card>
          <div className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Success Rate</div>
          <div className="text-2xl font-bold text-green-600">{stats.success_rate || 0}%</div>
        </Card>
        <Card>
          <div className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Failed</div>
          <div className="text-2xl font-bold text-red-600">{stats.failed_runs || 0}</div>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <h2 className={`text-lg font-semibold ${dark ? 'text-white' : ''}`}>Scheduled Tasks</h2>
        <button onClick={reloadConfig} className={`flex items-center gap-2 px-3 py-2 rounded-lg ${dark ? 'bg-gray-700 hover:bg-gray-600 text-gray-200' : 'bg-gray-100 hover:bg-gray-200'}`}>
          <RefreshCw size={16} />
          Reload
        </button>
      </div>

      {/* Tasks Grid */}
      {tasks.length === 0 ? (
        <Card className="text-center py-8">
          <Folder className={`w-12 h-12 mx-auto mb-3 ${dark ? 'text-gray-500' : 'text-gray-400'}`} />
          <p className={dark ? 'text-gray-400' : 'text-gray-500'}>No tasks configured</p>
          <p className={`text-sm ${dark ? 'text-gray-500' : 'text-gray-400'}`}>Deploy bots from Bot Factory tab</p>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tasks.map(task => (
            <Card key={task.name} className={!task.enabled ? 'opacity-60' : ''}>
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className={`font-semibold ${dark ? 'text-white' : ''}`}>{task.name}</h3>
                  <p className={`text-xs font-mono ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{task.script}</p>
                </div>
                <Toggle checked={task.enabled} onChange={(v) => toggleTask(task.name, v)} />
              </div>

              {task.description && (
                <p className={`text-sm mb-3 ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{task.description}</p>
              )}

              <div className={`flex flex-wrap gap-3 text-xs mb-3 py-2 border-t border-b ${dark ? 'text-gray-400 border-gray-700' : 'text-gray-500 border-gray-200'}`}>
                <span>Schedule: <code className={`px-1 rounded ${dark ? 'bg-gray-700' : 'bg-gray-100'}`}>{task.schedule || `${task.interval}s`}</code></span>
                <span>Runs: {task.run_count}</span>
                <span>Errors: {task.error_count}</span>
              </div>

              <div className="flex justify-between items-center">
                <StatusBadge status={task.last_status} running={task.running} />
                <div className="flex gap-2">
                  <button
                    onClick={() => runTask(task.name)}
                    disabled={task.running}
                    className="flex items-center gap-1 px-3 py-1.5 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600 disabled:opacity-50"
                  >
                    <Play size={14} />
                    {task.running ? 'Running...' : 'Run Now'}
                  </button>
                  <button
                    onClick={() => deleteTask(task.name)}
                    disabled={task.running}
                    className="flex items-center gap-1 px-2 py-1.5 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 disabled:opacity-50"
                    title="Delete bot permanently"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {task.next_run && (
                <p className={`text-xs mt-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>Next: {formatDate(task.next_run)}</p>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Run History */}
      <div>
        <h2 className={`text-lg font-semibold mb-3 ${dark ? 'text-white' : ''}`}>Recent Runs</h2>
        <Card className="overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className={dark ? 'bg-gray-700' : 'bg-gray-50'}>
              <tr>
                <th className={`text-left px-4 py-3 font-medium ${dark ? 'text-gray-300' : ''}`}>Task</th>
                <th className={`text-left px-4 py-3 font-medium ${dark ? 'text-gray-300' : ''}`}>Status</th>
                <th className={`text-left px-4 py-3 font-medium ${dark ? 'text-gray-300' : ''}`}>Started</th>
                <th className={`text-left px-4 py-3 font-medium ${dark ? 'text-gray-300' : ''}`}>Duration</th>
                <th className={`text-left px-4 py-3 font-medium ${dark ? 'text-gray-300' : ''}`}>Action</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${dark ? 'divide-gray-700' : ''}`}>
              {runs.map(run => (
                <tr key={run.id} className={dark ? 'hover:bg-gray-700/50' : 'hover:bg-gray-50'}>
                  <td className={`px-4 py-3 font-medium ${dark ? 'text-white' : ''}`}>{run.task_name}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={run.status} running={run.status === 'running'} />
                  </td>
                  <td className={`px-4 py-3 ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{formatDate(run.started_at)}</td>
                  <td className={`px-4 py-3 font-mono ${dark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '-'}
                  </td>
                  <td className="px-4 py-3 flex gap-2">
                    <button onClick={() => viewRunDetail(run.id)} className="text-blue-600 hover:underline">
                      Details
                    </button>
                    <button onClick={() => deleteRun(run.id)} className="text-red-600 hover:underline">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan="5" className={`px-4 py-8 text-center ${dark ? 'text-gray-400' : 'text-gray-500'}`}>
                    No runs yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>

      {/* Run Detail Modal */}
      {selectedRun && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedRun(null)}>
          <div className={`rounded-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden ${dark ? 'bg-gray-800' : 'bg-white'}`} onClick={e => e.stopPropagation()}>
            <div className={`flex justify-between items-center px-6 py-4 border-b ${dark ? 'border-gray-700' : ''}`}>
              <h3 className={`font-semibold ${dark ? 'text-white' : ''}`}>Run #{selectedRun.id}: {selectedRun.task_name}</h3>
              <button onClick={() => setSelectedRun(null)} className={`text-2xl ${dark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-400 hover:text-gray-600'}`}>&times;</button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className={`grid grid-cols-2 gap-4 mb-4 text-sm ${dark ? 'text-gray-300' : ''}`}>
                <div><strong>Status:</strong> {selectedRun.status}</div>
                <div><strong>Exit Code:</strong> {selectedRun.exit_code ?? '-'}</div>
                <div><strong>Started:</strong> {formatDate(selectedRun.started_at)}</div>
                <div><strong>Duration:</strong> {selectedRun.duration_seconds?.toFixed(2)}s</div>
              </div>

              {selectedRun.output && (
                <div className="mb-4">
                  <h4 className={`text-sm font-medium mb-2 ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Output</h4>
                  <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-48">
                    {selectedRun.output}
                  </pre>
                </div>
              )}

              {selectedRun.error && (
                <div>
                  <h4 className={`text-sm font-medium mb-2 ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Error</h4>
                  <pre className="bg-gray-900 text-red-400 p-4 rounded-lg text-xs overflow-x-auto max-h-48">
                    {selectedRun.error}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================================================
// Bot Factory Component
// ==================================================

function BotFactory({ onDeploy }) {
  const { dark } = useTheme();
  const [step, setStep] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [config, setConfig] = useState({
    botType: '',
    botName: '',
    botDescription: '',
    dataSources: {
      rss: { enabled: false, feeds: [] },
      api: { enabled: false, endpoints: [] },
      scraping: { enabled: false, urls: [] },
      weather: { enabled: false, location: '', apiKey: '' },
      homeassistant: { enabled: false, url: '', token: '', sensors: [] },
      zimaos: { enabled: false, url: 'http://172.17.0.1', username: '', password: '', metrics: ['system', 'cpu', 'memory', 'apps'] }
    },
    processing: {
      aiRewrite: false,
      aiProvider: 'anthropic',
      aiApiKey: '',
      deduplication: true
    },
    outputs: {
      email: { enabled: false, smtp: '', port: 465, user: '', pass: '', from: '', to: '' },
      telegram: { enabled: false, botToken: '', chatId: '' },
      discord: { enabled: false, webhookUrl: '' },
      slack: { enabled: false, webhookUrl: '' },
      pushover: { enabled: false, userKey: '', apiToken: '' }
    },
    schedule: {
      type: 'daily',
      time: '08:00',
      timezone: 'Europe/Berlin',
      interval: 60,
      cron: ''
    },
    professional: {
      healthCheck: { enabled: true },
      dashboard: { enabled: true, port: 8080 },
      retry: { enabled: true, maxRetries: 3 },
      structuredLogging: true,
      logLevel: 'INFO',
      dryRun: false
    }
  });

  const stepNames = ['Template', 'Type', 'Data', 'Process', 'Output', 'Schedule', 'Pro', 'Generate'];

  const botTypes = [
    { id: 'newsletter', name: 'Newsletter Bot', icon: Mail, desc: 'Collects content and sends newsletters' },
    { id: 'monitor', name: 'Monitor Bot', icon: Zap, desc: 'Monitors sources and alerts on changes' },
    { id: 'aggregator', name: 'Aggregator Bot', icon: Database, desc: 'Collects data from various sources' },
    { id: 'custom', name: 'Custom Bot', icon: Settings, desc: 'Fully customizable' }
  ];

  const applyTemplate = (template) => {
    setSelectedTemplate(template.id);
    setConfig(prev => ({
      ...template.config,
      dataSources: {
        ...template.config.dataSources,
        weather: { ...template.config.dataSources.weather, apiKey: prev.dataSources.weather.apiKey },
        homeassistant: { ...template.config.dataSources.homeassistant, token: prev.dataSources.homeassistant?.token || '' }
      },
      processing: {
        ...template.config.processing,
        aiApiKey: prev.processing.aiApiKey
      }
    }));
  };

  const updateConfig = (path, value) => {
    setConfig(prev => {
      const keys = path.split('.');
      const newConfig = JSON.parse(JSON.stringify(prev));
      let current = newConfig;
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      return newConfig;
    });
  };

  const deployBot = async () => {
    try {
      const res = await fetch('/api/bots/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const data = await res.json();
      if (data.status === 'ok') {
        alert(`Bot "${config.botName}" deployed!`);
        onDeploy?.();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (e) {
      alert(`Error: ${e.message}`);
    }
  };

  const downloadBot = async () => {
    const res = await fetch('/api/bots/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${config.botName || 'bot'}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Step Indicator
  const StepIndicator = () => (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-2">
        {stepNames.map((name, idx) => (
          <div key={idx} className="flex items-center">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-all ${
              idx < step ? 'bg-green-500 text-white' :
              idx === step ? 'bg-blue-600 text-white ring-4 ring-blue-200 dark:ring-blue-800' :
              dark ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-500'
            }`}>
              {idx < step ? '✓' : idx + 1}
            </div>
            {idx < stepNames.length - 1 && (
              <div className={`w-4 md:w-8 lg:w-12 h-1 mx-0.5 ${idx < step ? 'bg-green-500' : dark ? 'bg-gray-700' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs">
        {stepNames.map((name, idx) => (
          <span key={idx} className={`${idx === step ? 'text-blue-600 font-medium' : dark ? 'text-gray-500' : 'text-gray-400'}`}>{name}</span>
        ))}
      </div>
    </div>
  );

  // Render current step
  const renderStep = () => {
    switch(step) {
      case 0: // Templates
        return (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${dark ? 'text-white' : ''}`}>
              <Sparkles className="inline w-5 h-5 mr-2 text-yellow-500" />
              Choose a Template
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {botTemplates.map(template => (
                <Card
                  key={template.id}
                  selected={selectedTemplate === template.id}
                  onClick={() => applyTemplate(template)}
                >
                  <div className="flex items-start gap-3">
                    <template.icon className="w-8 h-8 text-blue-500 flex-shrink-0" />
                    <div>
                      <h3 className={`font-medium ${dark ? 'text-white' : ''}`}>{template.name}</h3>
                      <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{template.desc}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
            <p className={`text-center text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>
              Or skip templates and configure from scratch →
            </p>
          </div>
        );

      case 1: // Bot Type
        return (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${dark ? 'text-white' : ''}`}>Bot Type & Name</h2>
            <div className="grid md:grid-cols-2 gap-4 mb-6">
              {botTypes.map(type => (
                <Card
                  key={type.id}
                  selected={config.botType === type.id}
                  onClick={() => updateConfig('botType', type.id)}
                >
                  <div className="flex items-center gap-3">
                    <type.icon className="w-8 h-8 text-blue-500" />
                    <div>
                      <h3 className={`font-medium ${dark ? 'text-white' : ''}`}>{type.name}</h3>
                      <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{type.desc}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
            <Input
              label="Bot Name"
              value={config.botName}
              onChange={(v) => updateConfig('botName', v.replace(/[^a-z0-9-_]/gi, '-').toLowerCase())}
              placeholder="my-bot"
              required
            />
            <Input
              label="Description"
              value={config.botDescription}
              onChange={(v) => updateConfig('botDescription', v)}
              placeholder="What does this bot do?"
            />
          </div>
        );

      case 2: // Data Sources
        return (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${dark ? 'text-white' : ''}`}>Data Sources</h2>

            <Toggle
              label="RSS Feeds"
              checked={config.dataSources.rss.enabled}
              onChange={(v) => updateConfig('dataSources.rss.enabled', v)}
              description="Collect content from RSS/Atom feeds"
            />
            {config.dataSources.rss.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                {config.dataSources.rss.feeds.map((feed, i) => (
                  <div key={i} className="flex gap-2 mb-2">
                    <input
                      placeholder="Name"
                      value={feed.name}
                      onChange={(e) => {
                        const feeds = [...config.dataSources.rss.feeds];
                        feeds[i] = { ...feeds[i], name: e.target.value };
                        updateConfig('dataSources.rss.feeds', feeds);
                      }}
                      className={`flex-1 px-2 py-1 border rounded ${dark ? 'bg-gray-600 border-gray-500 text-white' : ''}`}
                    />
                    <input
                      placeholder="Feed URL"
                      value={feed.url}
                      onChange={(e) => {
                        const feeds = [...config.dataSources.rss.feeds];
                        feeds[i] = { ...feeds[i], url: e.target.value };
                        updateConfig('dataSources.rss.feeds', feeds);
                      }}
                      className={`flex-2 px-2 py-1 border rounded ${dark ? 'bg-gray-600 border-gray-500 text-white' : ''}`}
                    />
                    <button onClick={() => {
                      updateConfig('dataSources.rss.feeds', config.dataSources.rss.feeds.filter((_, idx) => idx !== i));
                    }} className="text-red-500"><Trash2 size={16} /></button>
                  </div>
                ))}
                <button
                  onClick={() => updateConfig('dataSources.rss.feeds', [...config.dataSources.rss.feeds, { name: '', url: '' }])}
                  className="flex items-center gap-1 text-blue-500 text-sm"
                >
                  <Plus size={14} /> Add Feed
                </button>
              </div>
            )}

            <Toggle
              label="REST API"
              checked={config.dataSources.api.enabled}
              onChange={(v) => updateConfig('dataSources.api.enabled', v)}
              description="Fetch data from REST APIs"
            />
            {config.dataSources.api.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                {config.dataSources.api.endpoints.map((ep, i) => (
                  <div key={i} className="flex gap-2 mb-2 items-center">
                    <input placeholder="Name" value={ep.name} onChange={(e) => {
                      const endpoints = [...config.dataSources.api.endpoints];
                      endpoints[i] = { ...endpoints[i], name: e.target.value };
                      updateConfig('dataSources.api.endpoints', endpoints);
                    }} className={`w-32 shrink-0 px-2 py-1 border rounded ${dark ? 'bg-gray-600 border-gray-500 text-white' : ''}`} />
                    <input placeholder="URL" value={ep.url} onChange={(e) => {
                      const endpoints = [...config.dataSources.api.endpoints];
                      endpoints[i] = { ...endpoints[i], url: e.target.value };
                      updateConfig('dataSources.api.endpoints', endpoints);
                    }} className={`flex-1 min-w-0 px-2 py-1 border rounded ${dark ? 'bg-gray-600 border-gray-500 text-white' : ''}`} />
                    <button onClick={() => {
                      updateConfig('dataSources.api.endpoints', config.dataSources.api.endpoints.filter((_, idx) => idx !== i));
                    }} className="text-red-500 shrink-0"><Trash2 size={16} /></button>
                  </div>
                ))}
                <button
                  onClick={() => updateConfig('dataSources.api.endpoints', [...config.dataSources.api.endpoints, { name: '', url: '', method: 'GET', headers: '{}', jsonPath: '' }])}
                  className="flex items-center gap-1 text-blue-500 text-sm"
                >
                  <Plus size={14} /> Add Endpoint
                </button>
              </div>
            )}

            <Toggle
              label="Web Scraping"
              checked={config.dataSources.scraping.enabled}
              onChange={(v) => updateConfig('dataSources.scraping.enabled', v)}
              description="Extract data from websites"
            />

            <Toggle
              label="Weather"
              checked={config.dataSources.weather.enabled}
              onChange={(v) => updateConfig('dataSources.weather.enabled', v)}
              description="OpenWeatherMap integration"
            />
            {config.dataSources.weather.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <Input label="Location" value={config.dataSources.weather.location} onChange={(v) => updateConfig('dataSources.weather.location', v)} placeholder="Berlin,DE" />
                <Input label="API Key" value={config.dataSources.weather.apiKey} onChange={(v) => updateConfig('dataSources.weather.apiKey', v)} type="password" />
              </div>
            )}

            <Toggle
              label="Home Assistant"
              checked={config.dataSources.homeassistant.enabled}
              onChange={(v) => updateConfig('dataSources.homeassistant.enabled', v)}
              description="Read sensors from Home Assistant"
            />
            {config.dataSources.homeassistant.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <Input label="URL" value={config.dataSources.homeassistant.url} onChange={(v) => updateConfig('dataSources.homeassistant.url', v)} placeholder="http://homeassistant.local:8123" />
                <Input label="Access Token" value={config.dataSources.homeassistant.token} onChange={(v) => updateConfig('dataSources.homeassistant.token', v)} type="password" />
              </div>
            )}

            <Toggle
              label="ZimaOS"
              checked={config.dataSources.zimaos?.enabled}
              onChange={(v) => updateConfig('dataSources.zimaos.enabled', v)}
              description="Monitor ZimaOS system (auto-login)"
            />
            {config.dataSources.zimaos?.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <Input label="ZimaOS URL" value={config.dataSources.zimaos?.url || ''} onChange={(v) => updateConfig('dataSources.zimaos.url', v)} placeholder="http://172.17.0.1" />
                <Input label="Username" value={config.dataSources.zimaos?.username || ''} onChange={(v) => updateConfig('dataSources.zimaos.username', v)} placeholder="ZimaOS username" />
                <Input label="Password" value={config.dataSources.zimaos?.password || ''} onChange={(v) => updateConfig('dataSources.zimaos.password', v)} type="password" placeholder="ZimaOS password" />
                <div className="mt-3">
                  <label className={`block text-sm font-medium mb-2 ${dark ? 'text-gray-300' : ''}`}>Metrics to collect</label>
                  <div className="flex flex-wrap gap-2">
                    {['system', 'cpu', 'memory', 'apps', 'storage'].map(metric => (
                      <label key={metric} className={`flex items-center gap-1 px-2 py-1 rounded ${dark ? 'bg-gray-600' : 'bg-gray-100'}`}>
                        <input
                          type="checkbox"
                          checked={config.dataSources.zimaos?.metrics?.includes(metric)}
                          onChange={(e) => {
                            const current = config.dataSources.zimaos?.metrics || [];
                            const updated = e.target.checked
                              ? [...current, metric]
                              : current.filter(m => m !== metric);
                            updateConfig('dataSources.zimaos.metrics', updated);
                          }}
                        />
                        <span className="text-sm capitalize">{metric}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case 3: // Processing
        return (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${dark ? 'text-white' : ''}`}>Processing</h2>

            <Toggle
              label="AI Processing"
              checked={config.processing.aiRewrite}
              onChange={(v) => updateConfig('processing.aiRewrite', v)}
              description="Use AI to process/summarize content"
            />
            {config.processing.aiRewrite && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <label className={`block text-sm font-medium mb-2 ${dark ? 'text-gray-300' : ''}`}>AI Provider</label>
                <select
                  value={config.processing.aiProvider}
                  onChange={(e) => updateConfig('processing.aiProvider', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg mb-3 ${dark ? 'bg-gray-600 border-gray-500 text-white' : ''}`}
                >
                  <option value="anthropic">Anthropic Claude</option>
                  <option value="openai">OpenAI GPT</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="ollama">Ollama (Local)</option>
                </select>
                <Input label="API Key" value={config.processing.aiApiKey} onChange={(v) => updateConfig('processing.aiApiKey', v)} type="password" />
              </div>
            )}

            <Toggle
              label="Deduplication"
              checked={config.processing.deduplication}
              onChange={(v) => updateConfig('processing.deduplication', v)}
              description="Skip already sent items"
            />
          </div>
        );

      case 4: // Output
        return (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${dark ? 'text-white' : ''}`}>Output Channels</h2>

            <Toggle label="Email" checked={config.outputs.email.enabled} onChange={(v) => updateConfig('outputs.email.enabled', v)} description="Send via SMTP" />
            {config.outputs.email.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg grid md:grid-cols-2 gap-3 ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <Input label="SMTP Server" value={config.outputs.email.smtp} onChange={(v) => updateConfig('outputs.email.smtp', v)} />
                <Input label="Port" value={config.outputs.email.port} onChange={(v) => updateConfig('outputs.email.port', v)} type="number" />
                <Input label="Username" value={config.outputs.email.user} onChange={(v) => updateConfig('outputs.email.user', v)} />
                <Input label="Password" value={config.outputs.email.pass} onChange={(v) => updateConfig('outputs.email.pass', v)} type="password" />
                <Input label="From" value={config.outputs.email.from} onChange={(v) => updateConfig('outputs.email.from', v)} />
                <Input label="To" value={config.outputs.email.to} onChange={(v) => updateConfig('outputs.email.to', v)} />
              </div>
            )}

            <Toggle label="Telegram" checked={config.outputs.telegram.enabled} onChange={(v) => updateConfig('outputs.telegram.enabled', v)} />
            {config.outputs.telegram.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <Input label="Bot Token" value={config.outputs.telegram.botToken} onChange={(v) => updateConfig('outputs.telegram.botToken', v)} type="password" />
                <Input label="Chat ID" value={config.outputs.telegram.chatId} onChange={(v) => updateConfig('outputs.telegram.chatId', v)} />
              </div>
            )}

            <Toggle label="Discord" checked={config.outputs.discord.enabled} onChange={(v) => updateConfig('outputs.discord.enabled', v)} />
            {config.outputs.discord.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <Input label="Webhook URL" value={config.outputs.discord.webhookUrl} onChange={(v) => updateConfig('outputs.discord.webhookUrl', v)} />
              </div>
            )}

            <Toggle label="Slack" checked={config.outputs.slack.enabled} onChange={(v) => updateConfig('outputs.slack.enabled', v)} />
            {config.outputs.slack.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <Input label="Webhook URL" value={config.outputs.slack.webhookUrl} onChange={(v) => updateConfig('outputs.slack.webhookUrl', v)} />
              </div>
            )}

            <Toggle label="Pushover" checked={config.outputs.pushover?.enabled} onChange={(v) => updateConfig('outputs.pushover.enabled', v)} />
            {config.outputs.pushover?.enabled && (
              <div className={`ml-4 mb-4 p-4 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <Input label="User Key" value={config.outputs.pushover?.userKey || ''} onChange={(v) => updateConfig('outputs.pushover.userKey', v)} />
                <Input label="API Token" value={config.outputs.pushover?.apiToken || ''} onChange={(v) => updateConfig('outputs.pushover.apiToken', v)} />
              </div>
            )}
          </div>
        );

      case 5: // Schedule
        return (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${dark ? 'text-white' : ''}`}>Schedule</h2>

            <div className="space-y-3 mb-6">
              {['daily', 'interval', 'cron'].map(type => (
                <Card key={type} selected={config.schedule.type === type} onClick={() => updateConfig('schedule.type', type)}>
                  <div className="flex items-center gap-3">
                    <Clock className="w-5 h-5 text-blue-500" />
                    <div>
                      <span className={`font-medium capitalize ${dark ? 'text-white' : ''}`}>{type}</span>
                      <span className={`text-sm ml-2 ${dark ? 'text-gray-400' : 'text-gray-500'}`}>
                        {type === 'daily' && '- Run once per day'}
                        {type === 'interval' && '- Run at fixed intervals'}
                        {type === 'cron' && '- Custom cron expression'}
                      </span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {config.schedule.type === 'daily' && (
              <Input label="Time" value={config.schedule.time} onChange={(v) => updateConfig('schedule.time', v)} type="time" />
            )}

            {config.schedule.type === 'interval' && (
              <div>
                <label className={`block text-sm font-medium mb-2 ${dark ? 'text-gray-300' : ''}`}>Interval (minutes)</label>
                <input
                  type="number"
                  value={config.schedule.interval}
                  onChange={(e) => updateConfig('schedule.interval', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-lg ${dark ? 'bg-gray-700 border-gray-600 text-white' : ''}`}
                  min="1"
                />
              </div>
            )}

            {config.schedule.type === 'cron' && (
              <Input
                label="Cron Expression"
                value={config.schedule.cron}
                onChange={(v) => updateConfig('schedule.cron', v)}
                placeholder="0 8 * * *"
                helpText="e.g., '0 8 * * *' = daily at 8:00"
              />
            )}

            <Input label="Timezone" value={config.schedule.timezone} onChange={(v) => updateConfig('schedule.timezone', v)} placeholder="Europe/Berlin" />
          </div>
        );

      case 6: // Professional
        return (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${dark ? 'text-white' : ''}`}>Professional Options</h2>

            <Toggle label="Health Check Endpoint" checked={config.professional.healthCheck.enabled} onChange={(v) => updateConfig('professional.healthCheck.enabled', v)} description="/health for Docker health checks" />
            <Toggle label="Web Dashboard" checked={config.professional.dashboard.enabled} onChange={(v) => updateConfig('professional.dashboard.enabled', v)} description="Status dashboard with run history" />
            <Toggle label="Retry on Error" checked={config.professional.retry.enabled} onChange={(v) => updateConfig('professional.retry.enabled', v)} description="Automatic retry with exponential backoff" />
            <Toggle label="Structured Logging" checked={config.professional.structuredLogging} onChange={(v) => updateConfig('professional.structuredLogging', v)} description="JSON formatted logs" />
            <Toggle label="Dry Run Mode" checked={config.professional.dryRun} onChange={(v) => updateConfig('professional.dryRun', v)} description="Test without sending outputs" />

            <div className="mt-4">
              <label className={`block text-sm font-medium mb-2 ${dark ? 'text-gray-300' : ''}`}>Log Level</label>
              <select
                value={config.professional.logLevel}
                onChange={(e) => updateConfig('professional.logLevel', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg ${dark ? 'bg-gray-700 border-gray-600 text-white' : ''}`}
              >
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>
          </div>
        );

      case 7: // Generate
        return (
          <div>
            <h2 className={`text-xl font-semibold mb-4 ${dark ? 'text-white' : ''}`}>Generate & Deploy</h2>

            <Card className="mb-6">
              <h3 className={`font-semibold mb-3 ${dark ? 'text-white' : ''}`}>Summary</h3>
              <div className={`grid md:grid-cols-2 gap-2 text-sm ${dark ? 'text-gray-300' : ''}`}>
                <div><strong>Name:</strong> {config.botName || '-'}</div>
                <div><strong>Type:</strong> {config.botType || '-'}</div>
                <div><strong>Schedule:</strong> {config.schedule.type === 'daily' ? `Daily at ${config.schedule.time}` : config.schedule.type === 'interval' ? `Every ${config.schedule.interval} min` : config.schedule.cron || '-'}</div>
                <div><strong>Outputs:</strong> {Object.entries(config.outputs).filter(([_,v]) => v.enabled).map(([k]) => k).join(', ') || 'None'}</div>
              </div>
            </Card>

            <div className="flex gap-4">
              <button
                onClick={deployBot}
                disabled={!config.botName}
                className="flex-1 flex items-center justify-center gap-2 bg-green-500 text-white py-3 rounded-xl font-medium hover:bg-green-600 disabled:opacity-50"
              >
                <Upload size={20} />
                Deploy to Task Manager
              </button>
              <button
                onClick={downloadBot}
                disabled={!config.botName}
                className="flex-1 flex items-center justify-center gap-2 bg-blue-500 text-white py-3 rounded-xl font-medium hover:bg-blue-600 disabled:opacity-50"
              >
                <Download size={20} />
                Download ZIP
              </button>
            </div>

            {!config.botName && (
              <p className="text-red-500 text-sm mt-2 text-center">Please enter a bot name in Step 2</p>
            )}
          </div>
        );
    }
  };

  return (
    <div>
      <StepIndicator />
      {renderStep()}

      {/* Navigation */}
      <div className={`flex justify-between mt-8 pt-4 border-t ${dark ? 'border-gray-700' : ''}`}>
        <button
          onClick={() => setStep(s => Math.max(0, s - 1))}
          disabled={step === 0}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg disabled:opacity-50 ${dark ? 'bg-gray-700 hover:bg-gray-600 text-gray-200' : 'bg-gray-100 hover:bg-gray-200'}`}
        >
          <ChevronLeft size={20} />
          Back
        </button>
        <button
          onClick={() => setStep(s => Math.min(stepNames.length - 1, s + 1))}
          disabled={step === stepNames.length - 1}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50"
        >
          Next
          <ChevronRight size={20} />
        </button>
      </div>
    </div>
  );
}

// ==================================================
// Main App
// ==================================================

export default function App() {
  const [activeTab, setActiveTab] = useState('tasks');
  const [dark, setDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' ||
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    }
    return false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  const tabs = [
    { id: 'tasks', name: 'Task Manager', icon: Clock },
    { id: 'factory', name: 'Bot Factory', icon: Bot },
  ];

  return (
    <ThemeContext.Provider value={{ dark, toggle: () => setDark(d => !d) }}>
      <div className={`min-h-screen ${dark ? 'bg-gray-900 text-gray-100' : 'bg-gray-50'}`}>
        {/* Header */}
        <header className={`${dark ? 'bg-gray-800 border-gray-700' : 'bg-white'} border-b`}>
          <div className="max-w-6xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bot className="w-8 h-8 text-blue-600" />
                <h1 className="text-xl font-bold">Bot Factory</h1>
              </div>
              <div className="flex items-center gap-4">
                <nav className={`flex gap-1 p-1 rounded-lg ${dark ? 'bg-gray-700' : 'bg-gray-100'}`}>
                  {tabs.map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
                        activeTab === tab.id
                          ? dark ? 'bg-gray-600 shadow text-blue-400' : 'bg-white shadow text-blue-600'
                          : dark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      <tab.icon size={18} />
                      <span className="hidden sm:inline">{tab.name}</span>
                    </button>
                  ))}
                </nav>
                <button
                  onClick={() => setDark(d => !d)}
                  className={`p-2 rounded-lg ${dark ? 'bg-gray-700 hover:bg-gray-600 text-yellow-400' : 'bg-gray-100 hover:bg-gray-200 text-gray-600'}`}
                >
                  {dark ? <Sun size={20} /> : <Moon size={20} />}
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-6xl mx-auto px-4 py-8">
          {activeTab === 'tasks' && <TaskManager />}
          {activeTab === 'factory' && <BotFactory onDeploy={() => setActiveTab('tasks')} />}
        </main>
      </div>
    </ThemeContext.Provider>
  );
}
