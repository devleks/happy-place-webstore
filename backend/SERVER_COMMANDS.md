# Server Quick Reference

## Start/Stop Commands

```bash
# Start server (Gunicorn with 4 workers)
./start_server.sh

# Stop server (graceful shutdown)
./stop_server.sh

# Restart server
./stop_server.sh && ./start_server.sh
```

## Check Status

```bash
# Health check
curl http://127.0.0.1:5001/api/pos/health

# View processes
ps aux | grep gunicorn

# Check port
lsof -i :5001
```

## View Logs

```bash
# Real-time access logs
tail -f server_access.log

# Real-time error logs
tail -f server.log

# Last 50 lines
tail -50 server.log
```

## Troubleshooting

```bash
# Force kill if stuck
lsof -ti:5001 | xargs kill -9

# Check if venv active
which gunicorn

# Test app
python -c "from app import create_app; create_app()"
```

## Configuration

- **Workers:** 4 (edit `start_server.sh` line 22)
- **Port:** 5001
- **Timeout:** 120 seconds
- **Logs:** `server.log` and `server_access.log`
- **PID File:** `gunicorn.pid`
