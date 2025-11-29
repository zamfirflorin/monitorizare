# Troubleshooting Guide

## Issues Fixed

### 1. **Prometheus Configuration**
- **Problem**: Used `host.docker.internal:8000` which doesn't work with Podman
- **Fix**: Changed to `host.containers.internal:8000` and added `extra_hosts` to Prometheus service
- **Note**: If `host.containers.internal` doesn't work, you may need to use your actual host IP address

### 2. **Elasticsearch/Kibana Security Mismatch**
- **Problem**: Elasticsearch had security disabled but Kibana expected credentials
- **Fix**: Disabled security in both Elasticsearch and Kibana configs

### 3. **Network Connectivity**
- Added `extra_hosts` to Prometheus service to enable host machine access

## Testing Steps

### 1. Start all services with Podman Compose:
```bash
podman-compose up -d
```

### 2. Verify services are running:
```bash
podman-compose ps
```

### 3. Start your Flask app:
```bash
source monitorizare_env/bin/activate
python app.py
```

### 4. Generate some traffic:
```bash
# In another terminal, make some requests
curl http://localhost:8090/login
curl http://localhost:8090/login
curl http://localhost:8090/login
```

### 5. Check each service:

#### **Prometheus** (http://localhost:9090)
- Go to Status → Targets
- Check if `login-service` target is UP
- Go to Graph and search for `login_total` or `login_duration_ms`

#### **Jaeger** (http://localhost:16686)
- Select service: `serviciu-login`
- Click "Find Traces"
- You should see traces from `/login` requests

#### **Kibana** (http://localhost:5601)
- Go to Stack Management → Index Patterns
- Create index pattern: `app-logs-*`
- Go to Discover to see logs

#### **Logstash**
- Check logs: `podman-compose logs logstash`
- Should see debug output if receiving data

## Alternative: If host.containers.internal doesn't work

If Prometheus still can't reach your Flask app, try:

1. Find your host IP:
   ```bash
   # On macOS
   ipconfig getifaddr en0
   # Or
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. Update `prometheus.yml`:
   ```yaml
   - targets: [ 'YOUR_HOST_IP:8000' ]
   ```

3. Restart Prometheus:
   ```bash
   podman-compose restart prometheus
   ```

## Common Issues

### No data in Prometheus
- Check if Flask app is running and metrics endpoint is accessible: `curl http://localhost:8000/metrics`
- Verify Prometheus can reach host: Check Prometheus logs with `podman-compose logs prometheus`

### No traces in Jaeger
- Verify Jaeger is receiving on port 6831: Check logs with `podman-compose logs jaeger`
- Make sure you're making requests to `/login` endpoint

### No logs in Kibana
- Check Elasticsearch has data: `curl http://localhost:9200/app-logs-*/_search?pretty`
- Check Logstash is running: `podman-compose logs logstash`
- Verify the log file exists: `ls -la /tmp/app.log`

