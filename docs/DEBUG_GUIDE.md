# MCP Server Debug Guide

This guide explains how to enable comprehensive debugging for the Semantic Scholar MCP server to troubleshoot issues.

## Quick Start - Enable Debug Mode

To enable full debugging for MCP server issues, set these environment variables:

```bash
export DEBUG_MCP_MODE=true
export LOG_MCP_MESSAGES=true
export LOG_API_PAYLOADS=true
export LOG_PERFORMANCE_METRICS=true
export MCP_MODE=true
```

Then restart Claude Desktop to pick up the new configuration.

## Environment Variables

### Core Debug Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG_MCP_MODE` | `false` | Master switch - enables all MCP debugging features |
| `DEBUG_LEVEL_OVERRIDE` | `null` | Override log level when debug mode is active (DEBUG, INFO, WARNING, ERROR) |
| `MCP_MODE` | `false` | Indicates running under MCP (auto-detected by Claude Desktop) |

### Detailed Logging Controls

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_MCP_MESSAGES` | `false` | Log MCP protocol messages and tool invocations |
| `LOG_API_PAYLOADS` | `false` | Log API request/response details |
| `LOG_PERFORMANCE_METRICS` | `false` | Log performance timing and metrics |

### API Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SEMANTIC_SCHOLAR_API_KEY` | `null` | Optional API key for higher rate limits |

## What Gets Logged

### 1. MCP Protocol Messages (`LOG_MCP_MESSAGES=true`)

- Tool execution start/end with timing
- Parameter validation and field extraction
- MCP tool context and correlation IDs
- Server startup/shutdown events

Example log entries:
```json
{
  "timestamp": "2025-07-08T10:30:00.000Z",
  "level": "DEBUG",
  "message": "Tool search_papers starting",
  "mcp_debug": true,
  "tool_name": "search_papers",
  "tool_operation": "execute",
  "correlation_id": "abc123..."
}
```

### 2. API Request/Response Details (`LOG_API_PAYLOADS=true`)

- HTTP method, URL, and parameters
- Response status codes and timing
- Content length and retry attempts
- Rate limit token information

Example log entries:
```json
{
  "timestamp": "2025-07-08T10:30:01.000Z",
  "level": "DEBUG", 
  "message": "API Request: GET https://api.semanticscholar.org/graph/v1/paper/search",
  "api_request": true,
  "method": "GET",
  "url": "https://api.semanticscholar.org/graph/v1/paper/search",
  "params": {"query": "machine learning", "limit": 10},
  "retry_attempt": 0,
  "rate_limit_tokens": 8
}
```

### 3. Circuit Breaker and Retry Logic

- Circuit breaker state changes (CLOSED → OPEN → HALF_OPEN)
- Retry attempts with exponential backoff details
- Failure thresholds and recovery timeouts

Example log entries:
```json
{
  "timestamp": "2025-07-08T10:30:02.000Z",
  "level": "INFO",
  "message": "Circuit breaker state: open",
  "circuit_breaker": true,
  "state": "open",
  "failure_count": 5,
  "failure_threshold": 5,
  "recovery_timeout": 60.0,
  "reason": "failure_threshold_exceeded"
}
```

### 4. Performance Metrics (`LOG_PERFORMANCE_METRICS=true`)

- Function execution timing
- Tool completion times
- API response times
- Cache hit/miss statistics

### 5. Enhanced Error Context

- Stack traces for debugging (when `DEBUG_MCP_MODE=true`)
- Detailed validation error information
- Exception chaining and context
- Request correlation across components

## Log Output Location

By default, logs are written to **stderr** to maintain MCP protocol compatibility (stdout is reserved for MCP communication).

When `DEBUG_MCP_MODE=true`, you can also configure file logging:

```bash
export LOGGING__FILE_PATH="/tmp/semantic-scholar-mcp-debug.log"
export LOGGING__FORMAT="json"  # or "text" for human-readable
```

## Troubleshooting Common Issues

### Issue: MCP Server Not Starting

Enable debug mode and check for:
```bash
export DEBUG_MCP_MODE=true
# Look for these in stderr:
# - "MCP server startup initiated"
# - Python path and import errors
# - Configuration validation errors
```

### Issue: Tools Not Responding

Enable tool tracing:
```bash
export LOG_MCP_MESSAGES=true
# Look for:
# - Tool execution start/completion
# - Parameter validation errors
# - MCP tool context information
```

### Issue: API Rate Limiting

Enable API payload logging:
```bash
export LOG_API_PAYLOADS=true
# Look for:
# - Rate limit token availability
# - 429 status codes
# - Retry attempts and backoff delays
```

### Issue: Network/API Errors

Check circuit breaker status and retry logic:
```bash
export DEBUG_MCP_MODE=true
# Look for:
# - Circuit breaker state changes
# - Network error details
# - Retry attempt logs with exponential backoff
```

## Performance Impact

Debug logging has minimal performance impact:

- **Debug Mode OFF**: Only ERROR level logs, ~0.1ms overhead per request
- **Debug Mode ON**: All debug logs, ~1-2ms overhead per request
- **API Payload Logging**: Additional ~0.5ms per API call

For production use, keep `DEBUG_MCP_MODE=false` unless actively troubleshooting.

## Log Analysis

### Finding Specific Tool Executions

Filter logs by correlation ID to trace a complete request:
```bash
grep "correlation_id.*abc123" /tmp/semantic-scholar-mcp-debug.log
```

### Analyzing API Performance

Check API response times:
```bash
grep "api_response.*true" /tmp/semantic-scholar-mcp-debug.log | jq '.response_time_ms'
```

### Circuit Breaker Health

Monitor circuit breaker state changes:
```bash
grep "circuit_breaker.*true" /tmp/semantic-scholar-mcp-debug.log | jq '.state'
```

## Production Recommendations

1. **Use API Key**: Set `SEMANTIC_SCHOLAR_API_KEY` for higher rate limits
2. **Monitor Logs**: Set up log rotation for debug files
3. **Health Checks**: Monitor circuit breaker states
4. **Rate Limits**: Adjust rate limiting based on API key tier

## Support Information

When reporting issues, please include:

1. Environment variables set
2. Relevant log entries (with correlation ID)
3. Claude Desktop version
4. Operating system
5. Network configuration (if applicable)

The enhanced logging provides comprehensive visibility into all MCP server operations for effective troubleshooting.