# Dashboard Setup Guide

## Overview

Semantic Scholar MCP includes a built-in web dashboard for monitoring and analytics, inspired by Serena's architecture. The dashboard provides real-time insights into tool usage, search analytics, performance metrics, and server health.

## Features

### 📊 Dashboard Sections

1. **Server Status**
   - Total tool calls
   - Total errors
   - Cache hit rate
   - PDF conversion count

2. **Real-time Logs**
   - Auto-polling (5-second intervals)
   - Log level filtering
   - Auto-scroll functionality

3. **Tool Usage Statistics**
   - Tool invocation counts
   - Error tracking

4. **Search Analytics**
   - Top search queries
   - Most accessed papers
   - Field distribution (Chart.js visualization)

5. **Performance Metrics**
   - API cache hit rate
   - Response time metrics
   - PDF processing statistics

6. **Theme Toggle**
   - Light/Dark mode support

## Quick Start

### 1. Enable Dashboard

Edit your `.env` file:

```bash
# Dashboard Configuration
DASHBOARD__ENABLED=true
DASHBOARD__OPEN_ON_LAUNCH=true
DASHBOARD__PORT=25000  # Default port
```

### 2. Start MCP Server

```bash
uv run semantic-scholar-mcp
```

### 3. Access Dashboard

The dashboard will automatically open in your default browser at:
```
http://127.0.0.1:25000/dashboard/
```

## Port Configuration

### ⚠️ Important: Port Conflict Warning

**Default Port**: `25000`

The dashboard previously used port `24282` (0x5EDA), which **conflicts with Serena's default port**. If you're running Serena and Semantic Scholar MCP on the same machine, they will compete for the same port.

### Port Conflict Resolution

#### Check for Port Conflicts

Before starting the dashboard, verify the port is available:

```bash
# Check if port 25000 is in use
netstat -tln | grep 25000

# Or using ss
ss -tln | grep 25000

# Check what's using dashboard ports
lsof -i :25000
```

#### Common Port Conflicts

| Service | Default Port | Conflict Risk |
|---------|-------------|---------------|
| Serena Dashboard | 24282 (0x5EDA) | ⚠️ Avoided (auto-fallback from 25000) |
| Semantic Scholar MCP | 25000 (auto-scan start) | ✅ Safe |
| Multiple MCP Instances | 25001-25009 | Auto-fallback enabled |

### Custom Port Configuration

#### Method 1: Environment Variable (Recommended)

```bash
# .env file
DASHBOARD__PORT=26000  # Use any available port
```

#### Method 2: Command Line

```bash
DASHBOARD__PORT=26000 uv run semantic-scholar-mcp
```

#### Method 3: Code Configuration

Edit `src/core/config.py`:

```python
class DashboardConfig(BaseModel):
    port: int = Field(default=26000, ge=1024, le=65535)
```

### Port Auto-Fallback

The dashboard includes automatic port fallback:

1. Starts scanning from port 25000 (to avoid Serena's default 24282)
2. Finds first available port (25000, 25001, 25002, ...)
3. Logs the actual port in use

**Example log output:**
```
Dashboard started at http://0.0.0.0:25000/dashboard/
```

If port 25000 is busy, it automatically tries 25001, 25002, etc.

## Configuration Reference

### Environment Variables

```bash
# Enable/disable dashboard
DASHBOARD__ENABLED=true              # Default: false

# Network settings
DASHBOARD__PORT=25000                # Default: 25000
# Note: Host is always 0.0.0.0 (listens on all interfaces)

# Browser behavior
DASHBOARD__OPEN_ON_LAUNCH=true      # Default: true

# Performance tuning
DASHBOARD__AUTO_REFRESH_SECONDS=5   # Default: 5 (not in .env by default)
DASHBOARD__MAX_LOG_MESSAGES=1000    # Default: 1000 (not in .env by default)
```

### Full Configuration Example

```bash
# .env
# Dashboard (Serena-style monitoring UI)
# Note: Using port 25000 to avoid conflict with Serena (24282)
DASHBOARD__ENABLED=true
DASHBOARD__OPEN_ON_LAUNCH=true
DASHBOARD__PORT=25000
```

## API Endpoints

The dashboard exposes the following REST API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard/` | GET | Main HTML UI |
| `/dashboard/<filename>` | GET | Static files (CSS/JS) |
| `/api/health` | GET | Health check |
| `/api/logs` | POST | Fetch log messages |
| `/api/stats` | GET | Tool usage statistics |
| `/api/analytics` | GET | Search analytics |
| `/api/performance` | GET | Performance metrics |
| `/api/stats/clear` | POST | Clear statistics |

### Example API Usage

```bash
# Health check
curl http://127.0.0.1:25000/api/health

# Get statistics
curl http://127.0.0.1:25000/api/stats

# Get logs (POST with JSON body)
curl -X POST http://127.0.0.1:25000/api/logs \
  -H "Content-Type: application/json" \
  -d '{"start_idx": 0}'
```

## Troubleshooting

### Dashboard Not Starting

1. **Check if port is already in use:**
   ```bash
   netstat -tln | grep 25000
   ```

2. **Check dashboard is enabled in .env:**
   ```bash
   grep DASHBOARD .env
   ```

3. **Verify configuration loads correctly:**
   ```bash
   uv run python -c "
   from core.config import ApplicationConfig
   config = ApplicationConfig()
   print(f'Enabled: {config.dashboard.enabled}')
   print(f'Port: {config.dashboard.port}')
   "
   ```

### Dashboard Shows 404 Not Found

- **Correct URL format:** `http://127.0.0.1:25000/dashboard/` (note the trailing slash)
- **Incorrect:** `http://127.0.0.1:25000/` (missing `/dashboard/`)

### Port Already in Use

If you see this error:
```
Configured dashboard port 25000 on host 0.0.0.0 is unavailable
```

**Solution 1:** Let auto-fallback choose a port
- Check the logs for the actual port: `Dashboard started at http://0.0.0.0:25001/dashboard/`

**Solution 2:** Choose a different port manually
```bash
DASHBOARD__PORT=26000 uv run semantic-scholar-mcp
```

**Solution 3:** Find and stop the conflicting process
```bash
# Find what's using the port
lsof -i :25000

# Stop the process (if safe to do so)
kill <PID>
```

### Running Multiple MCP Instances

If you need to run multiple Semantic Scholar MCP instances:

```bash
# Instance 1
DASHBOARD__PORT=25000 uv run semantic-scholar-mcp

# Instance 2
DASHBOARD__PORT=25001 uv run semantic-scholar-mcp

# Instance 3
DASHBOARD__PORT=25002 uv run semantic-scholar-mcp
```

## Architecture

### Backend (Python/Flask)

- **Framework:** Flask 3.x
- **Threading:** Daemon thread for non-blocking operation
- **Stats Collection:** Thread-safe DashboardStats class

### Frontend

- **HTML/CSS:** Responsive design with CSS variables
- **JavaScript:** Vanilla JS (no frameworks)
- **Charts:** Chart.js 4.4.0 for visualizations

### Comparison with Serena

| Feature | Serena | Semantic Scholar MCP |
|---------|--------|---------------------|
| Framework | Flask | Flask ✅ |
| Threading | Daemon thread | Daemon thread ✅ |
| Default Port | 24282 (0x5EDA) | 25000 (auto-scan start) |
| Real-time Logs | ✅ | ✅ |
| Tool Statistics | ✅ | ✅ |
| Charts | jQuery + Chart.js | Vanilla JS + Chart.js |
| Dark Mode | ✅ | ✅ |
| Browser Auto-launch | ✅ | ✅ |
| Search Analytics | ❌ | ✅ (unique feature) |
| PDF Metrics | ❌ | ✅ (unique feature) |

## Security Considerations

### Local-only Access (Default)

The dashboard listens on `0.0.0.0` but is intended for local development:

- **No authentication** by default
- **Read-only** monitoring (except `/api/stats/clear`)
- Designed for **local development environments**

### Production Deployment

For production use, consider:

1. **Disable dashboard:**
   ```bash
   DASHBOARD__ENABLED=false
   ```

2. **Use reverse proxy with authentication:**
   ```nginx
   location /dashboard/ {
       auth_basic "Restricted";
       auth_basic_user_file /etc/nginx/.htpasswd;
       proxy_pass http://127.0.0.1:25000/dashboard/;
   }
   ```

3. **Bind to localhost only** (requires code modification)

## Contributing

If you encounter issues or have suggestions for the dashboard:

1. Check existing issues: https://github.com/hy20191108/semantic-scholar-mcp/issues
2. Report port conflicts with details about your environment
3. Submit pull requests for improvements

## References

- **Serena Dashboard:** Inspiration for this implementation
- **Chart.js Documentation:** https://www.chartjs.org/docs/latest/
- **Flask Documentation:** https://flask.palletsprojects.com/
