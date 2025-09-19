# Hướng Dẫn Triển Khai Đa Người Dùng - Seed-VC CPU

## 🏗️ Kiến Trúc Multi-User

Hệ thống Seed-VC CPU đã được tối ưu hóa để xử lý nhiều người dùng cùng lúc với các thành phần sau:

### 🔧 Thành Phần Hệ Thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Frontend      │    │   Backend       │
│   (HAProxy)     │────│   (Next.js)     │────│   (FastAPI)     │
│   Port 80/443   │    │   Multiple      │    │   Multiple      │
└─────────────────┘    │   Instances     │    │   Instances     │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cluster │    │   Worker Pool   │    │   File Storage  │
│   (Caching +    │    │   (CPU Tasks)   │    │   (User Files)  │
│   Session Mgmt) │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🚀 Tính Năng Tối Ưu Multi-User

#### 1. **Load Balancing & High Availability**
- **HAProxy**: Phân phối tải thông minh với health checks
- **Multiple Frontend Instances**: Nhiều server Next.js chạy song song
- **Multiple Backend Instances**: API servers với auto-scaling
- **Redis Sentinel**: High availability cho cache và sessions

#### 2. **Concurrent Processing**
- **Worker Pool Management**: Process pools cho audio processing
- **Queue Priority System**: Hàng đợi ưu tiên với Redis
- **Resource Isolation**: Mỗi user có workspace riêng
- **Rate Limiting**: Giới hạn requests per user/IP

#### 3. **Real-time Communication**
- **WebSocket Clustering**: Real-time updates cho tất cả users
- **Session Management**: Persistent sessions với Redis
- **Live Progress Tracking**: Theo dõi tiến trình real-time
- **Instant Notifications**: Thông báo kết quả ngay lập tức

#### 4. **Performance Optimization**
- **CPU Affinity**: Gán worker processes cho CPU cores cụ thể
- **Memory Management**: Intelligent caching và cleanup
- **Disk I/O Optimization**: Async file operations
- **Network Optimization**: Connection pooling và keep-alive

## 📊 Khả Năng Xử Lý Theo Cấu Hình

### Cấu Hình Cơ Bản (4 CPU, 8GB RAM)
```bash
# Triển khai cho 10-20 người dùng đồng thời
./scripts/deploy-multiuser.sh systemd 2 20

# Kết quả:
# - 2 Backend instances
# - 2 Frontend instances  
# - 4 Worker processes
# - Throughput: ~10 jobs/phút
```

### Cấu Hình Tiêu Chuẩn (8 CPU, 16GB RAM)
```bash
# Triển khai cho 30-50 người dùng đồng thời
./scripts/deploy-multiuser.sh docker 3 50

# Kết quả:
# - 3 Backend instances
# - 3 Frontend instances
# - 8 Worker processes
# - Throughput: ~25 jobs/phút
```

### Cấu Hình Cao Cấp (16 CPU, 32GB RAM)
```bash
# Triển khai cho 50-100 người dùng đồng thời
./scripts/deploy-multiuser.sh docker 4 100

# Kết quả:
# - 4 Backend instances
# - 4 Frontend instances
# - 16 Worker processes
# - Throughput: ~50 jobs/phút
```

### Cấu Hình Enterprise (32+ CPU, 64+ GB RAM)
```bash
# Triển khai cho 100+ người dùng đồng thời
./scripts/deploy-multiuser.sh docker 6 200

# Kết quả:
# - 6 Backend instances
# - 6 Frontend instances
# - 32 Worker processes
# - Throughput: ~100+ jobs/phút
```

## 🛠️ Tùy Chỉnh Hiệu Suất

### Điều Chỉnh Worker Processes

```bash
# Trong runtime, có thể scale workers động
curl -X POST "http://your-server/api/system/scale" \
  -H "Content-Type: application/json" \
  -d '{"new_worker_count": 8}'
```

### Cấu Hình Redis Clustering

```yaml
# docker-compose.production.yml
redis-cluster:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
  volumes:
    - redis_cluster_data:/data
```

### Tối Ưu Nginx/HAProxy

```nginx
# Tăng connection limits
worker_processes auto;
worker_connections 4096;
keepalive_requests 1000;

# Load balancing algorithms
upstream backend {
    least_conn;  # Ít kết nối nhất
    # ip_hash;   # Sticky sessions
    # round_robin; # Luân phiên
}
```

## 🔍 Monitoring & Analytics

### Real-time Monitoring

```bash
# Giám sát system real-time
./monitor_multiuser.sh

# Kiểm tra performance metrics
curl http://your-server/api/system/stats

# Xem HAProxy stats
curl http://your-server:8404/stats
```

### Dashboard URLs

- **Application**: `http://your-server`
- **HAProxy Stats**: `http://your-server:8404`
- **Grafana Dashboard**: `http://your-server:3001`
- **Prometheus Metrics**: `http://your-server:9090`

### Key Metrics để Monitor

1. **User Metrics**:
   - Concurrent users
   - Requests per second
   - Average response time
   - Error rates

2. **System Metrics**:
   - CPU utilization per core
   - Memory usage patterns
   - Disk I/O rates
   - Network bandwidth

3. **Application Metrics**:
   - Queue length
   - Processing times
   - Worker utilization
   - Cache hit rates

## 🔒 Security & Rate Limiting

### Rate Limiting Configuration

```python
# Cấu hình rate limiting trong backend
RATE_LIMITS = {
    "api_general": {"limit": 30, "window": 60},      # 30 req/min
    "convert": {"limit": 5, "window": 60},           # 5 conversions/min
    "clone": {"limit": 3, "window": 3600},           # 3 cloning jobs/hour
    "upload": {"limit": 10, "window": 300}           # 10 uploads/5min
}
```

### Security Headers

```nginx
# Nginx security configuration
add_header Strict-Transport-Security "max-age=31536000";
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

## 📈 Scaling Strategies

### Horizontal Scaling (Khuyến nghị)

```bash
# Thêm servers
docker-compose -f docker-compose.production.yml up -d --scale backend=6 --scale frontend=4

# Auto-scaling với Docker Swarm
docker service update --replicas 8 seed-vc-backend
```

### Vertical Scaling

```bash
# Tăng resources cho containers
docker-compose -f docker-compose.production.yml up -d \
  --scale backend=4 \
  -e BACKEND_MEMORY=4G \
  -e BACKEND_CPU=2
```

### Database Scaling (Nếu cần)

```yaml
# PostgreSQL với connection pooling
postgres:
  image: postgres:15
  environment:
    - POSTGRES_MAX_CONNECTIONS=200
    - POSTGRES_SHARED_BUFFERS=256MB
```

## 🎯 Best Practices cho Production

### 1. **Resource Management**
```bash
# Giới hạn memory per process
ulimit -v 2097152  # 2GB virtual memory limit

# Giới hạn CPU time
ulimit -t 300      # 5 minutes CPU time limit

# File descriptor limits
ulimit -n 65536    # Increase file descriptors
```

### 2. **Process Management**
```bash
# Sử dụng process managers
systemctl enable seed-vc-*
systemctl set-property seed-vc-backend-1 CPUQuota=200%
systemctl set-property seed-vc-backend-1 MemoryMax=4G
```

### 3. **Backup & Recovery**
```bash
# Backup models và configurations
tar -czf backup-$(date +%Y%m%d).tar.gz models/ backend/models_config.json

# Backup Redis data
redis-cli --rdb dump.rdb

# Automated backup script
cat > backup.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "backup_$DATE.tar.gz" models/ uploads/ outputs/ backend/models_config.json
aws s3 cp "backup_$DATE.tar.gz" s3://your-backup-bucket/
EOF
```

## 🐛 Troubleshooting Multi-User Issues

### Vấn Đề Thường Gặp

#### 1. **High CPU Usage**
```bash
# Kiểm tra top processes
htop -d 1

# Giảm số workers
curl -X POST "http://localhost/api/system/scale" -d '{"new_worker_count": 4}'

# Limit CPU per process
systemctl set-property seed-vc-backend-1 CPUQuota=100%
```

#### 2. **Memory Leaks**
```bash
# Monitor memory usage
watch 'free -m'

# Restart services định kỳ
sudo systemctl restart seed-vc-backend-*

# Clear Redis cache
redis-cli FLUSHALL
```

#### 3. **Queue Backlog**
```bash
# Kiểm tra queue status
curl http://localhost/api/queue/status

# Clear queue nếu cần
redis-cli DEL job_queue

# Tăng workers tạm thời
curl -X POST "http://localhost/api/system/scale" -d '{"new_worker_count": 8}'
```

#### 4. **WebSocket Connection Issues**
```bash
# Kiểm tra WebSocket connections
netstat -an | grep :8000 | grep ESTABLISHED

# Restart với WebSocket debugging
export DEBUG=websocket*
systemctl restart seed-vc-backend-*
```

## 📋 Production Checklist

### Pre-Deployment
- [ ] Kiểm tra system requirements
- [ ] Configure firewall rules
- [ ] Setup SSL certificates
- [ ] Configure monitoring
- [ ] Setup backup strategy
- [ ] Load testing

### Deployment
- [ ] Deploy with docker-compose.production.yml
- [ ] Verify all services are healthy
- [ ] Test load balancer
- [ ] Verify Redis clustering
- [ ] Test WebSocket connections
- [ ] Run performance tests

### Post-Deployment
- [ ] Monitor system metrics
- [ ] Setup log aggregation
- [ ] Configure alerts
- [ ] Document procedures
- [ ] Train operations team
- [ ] Plan scaling strategy

## 🎯 Kết Luận

Hệ thống Seed-VC CPU đã được tối ưu hoàn toàn cho việc phục vụ nhiều người dùng đồng thời với:

✅ **Khả năng mở rộng**: Từ 10 đến 100+ người dùng đồng thời
✅ **High Availability**: Load balancing với failover tự động  
✅ **Real-time Updates**: WebSocket với clustering support
✅ **Performance Monitoring**: Dashboard và metrics chi tiết
✅ **Resource Optimization**: CPU/Memory management thông minh
✅ **100% Tiếng Việt**: Giao diện và documentation hoàn chỉnh

Hệ thống sẵn sàng triển khai production cho traffic cao! 🚀