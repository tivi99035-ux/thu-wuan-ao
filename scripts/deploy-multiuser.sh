#!/bin/bash

# Seed-VC CPU Multi-User Deployment Script
# Optimized for high-concurrency and multiple users

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_MODE=${1:-"production"}
SCALE_FACTOR=${2:-"2"}  # Number of replicas per service
MAX_CONCURRENT_USERS=${3:-"50"}

echo -e "${PURPLE}================================================${NC}"
echo -e "${PURPLE}  Seed-VC CPU Multi-User Deployment Script     ${NC}"
echo -e "${PURPLE}  Chế độ: $DEPLOYMENT_MODE                     ${NC}"
echo -e "${PURPLE}  Tỷ lệ scale: $SCALE_FACTOR replicas          ${NC}"
echo -e "${PURPLE}  Người dùng đồng thời: $MAX_CONCURRENT_USERS  ${NC}"
echo -e "${PURPLE}================================================${NC}"

# Check system requirements
check_system_requirements() {
    echo -e "${YELLOW}Kiểm tra yêu cầu hệ thống...${NC}"
    
    # Check CPU cores
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 4 ]; then
        echo -e "${RED}Cảnh báo: Hệ thống chỉ có $CPU_CORES CPU cores. Khuyến nghị ít nhất 4 cores cho multi-user.${NC}"
    else
        echo -e "${GREEN}✓ CPU: $CPU_CORES cores${NC}"
    fi
    
    # Check RAM
    TOTAL_RAM=$(free -g | awk 'NR==2{print $2}')
    if [ "$TOTAL_RAM" -lt 8 ]; then
        echo -e "${RED}Cảnh báo: Hệ thống chỉ có ${TOTAL_RAM}GB RAM. Khuyến nghị ít nhất 8GB cho multi-user.${NC}"
    else
        echo -e "${GREEN}✓ RAM: ${TOTAL_RAM}GB${NC}"
    fi
    
    # Check disk space
    DISK_SPACE=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "${DISK_SPACE%%G}" -lt 50 ]; then
        echo -e "${RED}Cảnh báo: Chỉ còn ${DISK_SPACE} dung lượng disk. Khuyến nghị ít nhất 50GB trống.${NC}"
    else
        echo -e "${GREEN}✓ Disk: ${DISK_SPACE} available${NC}"
    fi
}

# Optimize system for multi-user
optimize_system() {
    echo -e "${YELLOW}Tối ưu hệ thống cho đa người dùng...${NC}"
    
    # Increase file descriptor limits
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "root soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "root hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    
    # Optimize kernel parameters
    sudo tee -a /etc/sysctl.conf > /dev/null <<EOF
# Seed-VC CPU Multi-User Optimizations
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF
    
    # Apply kernel parameters
    sudo sysctl -p
    
    echo -e "${GREEN}✓ Hệ thống đã được tối ưu${NC}"
}

# Deploy with Docker Compose
deploy_docker_production() {
    echo -e "${YELLOW}Triển khai production với Docker...${NC}"
    
    # Create necessary directories
    mkdir -p {models,uploads,outputs,logs,ssl,monitoring}
    
    # Generate SSL certificates if not exist
    if [ ! -f "ssl/cert.pem" ]; then
        echo -e "${YELLOW}Tạo SSL certificates...${NC}"
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/key.pem \
            -out ssl/cert.pem \
            -subj "/C=VN/ST=Vietnam/L=HoChiMinh/O=SeedVC/CN=localhost"
    fi
    
    # Build and deploy
    echo -e "${YELLOW}Build và khởi động containers...${NC}"
    
    # Stop existing services
    docker-compose -f docker-compose.production.yml down || true
    
    # Build images
    docker-compose -f docker-compose.production.yml build --parallel
    
    # Start services with scaling
    docker-compose -f docker-compose.production.yml up -d
    
    # Scale services based on requirements
    echo -e "${YELLOW}Scaling services cho $MAX_CONCURRENT_USERS người dùng đồng thời...${NC}"
    
    # Calculate optimal scaling
    BACKEND_REPLICAS=$((MAX_CONCURRENT_USERS / 20 + 1))  # 20 users per backend
    FRONTEND_REPLICAS=$((MAX_CONCURRENT_USERS / 30 + 1)) # 30 users per frontend
    
    # Cap at reasonable limits
    BACKEND_REPLICAS=$([ $BACKEND_REPLICAS -gt 6 ] && echo 6 || echo $BACKEND_REPLICAS)
    FRONTEND_REPLICAS=$([ $FRONTEND_REPLICAS -gt 4 ] && echo 4 || echo $FRONTEND_REPLICAS)
    
    echo -e "${BLUE}Scaling: ${BACKEND_REPLICAS} backend, ${FRONTEND_REPLICAS} frontend instances${NC}"
    
    # Wait for services to be ready
    echo -e "${YELLOW}Đợi services khởi động...${NC}"
    sleep 30
    
    # Health checks
    check_services_health
}

# Deploy without Docker (systemd)
deploy_systemd_production() {
    echo -e "${YELLOW}Triển khai production với systemd...${NC}"
    
    # Stop existing services
    sudo systemctl stop seed-vc-* || true
    
    # Install dependencies
    source venv/bin/activate
    pip install -r backend/requirements.txt
    
    # Build frontend
    pnpm run build --no-lint
    
    # Create systemd services for multiple instances
    create_systemd_services
    
    # Start Redis if not running
    sudo systemctl start redis-server || sudo systemctl start redis
    sudo systemctl enable redis-server || sudo systemctl enable redis
    
    # Start services
    start_systemd_services
    
    # Setup Nginx load balancing
    setup_nginx_load_balancing
    
    # Health checks
    check_services_health
}

create_systemd_services() {
    echo -e "${YELLOW}Tạo systemd services cho multi-user...${NC}"
    
    # Backend services (multiple instances)
    for i in $(seq 1 $SCALE_FACTOR); do
        PORT=$((8000 + i - 1))
        
        sudo tee /etc/systemd/system/seed-vc-backend-$i.service > /dev/null <<EOF
[Unit]
Description=Seed-VC Backend Instance $i
After=network.target redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
Environment=REDIS_URL=redis://localhost:6379/0
Environment=WORKER_ID=backend-$i
Environment=MAX_WORKERS=4
Environment=MAX_QUEUE_SIZE=$((200 / SCALE_FACTOR))
ExecStart=$PWD/venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT --app-dir backend --workers 1
Restart=always
RestartSec=3
StandardOutput=append:$PWD/logs/backend-$i.log
StandardError=append:$PWD/logs/backend-$i-error.log
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
    done
    
    # Frontend services (multiple instances)
    for i in $(seq 1 $SCALE_FACTOR); do
        PORT=$((3000 + i - 1))
        
        sudo tee /etc/systemd/system/seed-vc-frontend-$i.service > /dev/null <<EOF
[Unit]
Description=Seed-VC Frontend Instance $i
After=network.target seed-vc-backend-$i.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=NODE_ENV=production
Environment=PORT=$PORT
Environment=NEXT_PUBLIC_API_URL=http://localhost/api
Environment=SERVER_ID=frontend-$i
ExecStart=/usr/bin/pnpm start
Restart=always
RestartSec=3
StandardOutput=append:$PWD/logs/frontend-$i.log
StandardError=append:$PWD/logs/frontend-$i-error.log
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
    done
    
    # Reload systemd
    sudo systemctl daemon-reload
}

start_systemd_services() {
    echo -e "${YELLOW}Khởi động systemd services...${NC}"
    
    # Start backend instances
    for i in $(seq 1 $SCALE_FACTOR); do
        sudo systemctl start seed-vc-backend-$i
        sudo systemctl enable seed-vc-backend-$i
        echo -e "${GREEN}✓ Backend instance $i started${NC}"
        sleep 2
    done
    
    # Start frontend instances
    for i in $(seq 1 $SCALE_FACTOR); do
        sudo systemctl start seed-vc-frontend-$i
        sudo systemctl enable seed-vc-frontend-$i
        echo -e "${GREEN}✓ Frontend instance $i started${NC}"
        sleep 2
    done
}

setup_nginx_load_balancing() {
    echo -e "${YELLOW}Cấu hình Nginx load balancing...${NC}"
    
    # Create Nginx configuration for load balancing
    sudo tee /etc/nginx/sites-available/seed-vc-multiuser > /dev/null <<EOF
# Seed-VC CPU Multi-User Nginx Configuration

upstream backend_servers {
    least_conn;
    $(for i in $(seq 1 $SCALE_FACTOR); do echo "    server 127.0.0.1:$((8000 + i - 1)) max_fails=3 fail_timeout=30s;"; done)
    keepalive 32;
}

upstream frontend_servers {
    least_conn;
    $(for i in $(seq 1 $SCALE_FACTOR); do echo "    server 127.0.0.1:$((3000 + i - 1)) max_fails=3 fail_timeout=30s;"; done)
    keepalive 32;
}

# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=upload:10m rate=2r/s;
limit_req_zone \$binary_remote_addr zone=clone:10m rate=1r/m;

server {
    listen 80;
    listen 443 ssl http2;
    server_name _;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend_servers;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # WebSocket endpoint
    location /ws {
        proxy_pass http://backend_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # Upload endpoints with special handling
    location ~ ^/api/(convert|clone) {
        limit_req zone=upload burst=5 nodelay;
        
        # Special rate limiting for cloning
        if (\$uri ~ "/clone") {
            limit_req zone=clone burst=1 nodelay;
        }
        
        proxy_pass http://backend_servers;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Extended timeouts for file processing
        proxy_connect_timeout 60s;
        proxy_send_timeout 900s;
        proxy_read_timeout 900s;
        client_max_body_size 100M;
    }
    
    # Static files (results)
    location /static/ {
        proxy_pass http://backend_servers;
        expires 1h;
        add_header Cache-Control "public";
    }
    
    # Frontend
    location / {
        proxy_pass http://frontend_servers;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support for Next.js
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/seed-vc-multiuser /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test and reload Nginx
    sudo nginx -t && sudo systemctl reload nginx
}

check_services_health() {
    echo -e "${YELLOW}Kiểm tra tình trạng services...${NC}"
    
    # Wait for services to be ready
    sleep 10
    
    # Check backend instances
    for i in $(seq 1 $SCALE_FACTOR); do
        PORT=$((8000 + i - 1))
        if curl -s http://localhost:$PORT/health > /dev/null; then
            echo -e "${GREEN}✓ Backend instance $i (port $PORT) đang hoạt động${NC}"
        else
            echo -e "${RED}✗ Backend instance $i (port $PORT) không phản hồi${NC}"
        fi
    done
    
    # Check frontend instances
    for i in $(seq 1 $SCALE_FACTOR); do
        PORT=$((3000 + i - 1))
        if curl -s http://localhost:$PORT > /dev/null; then
            echo -e "${GREEN}✓ Frontend instance $i (port $PORT) đang hoạt động${NC}"
        else
            echo -e "${RED}✗ Frontend instance $i (port $PORT) không phản hồi${NC}"
        fi
    done
    
    # Check load balancer
    if curl -s http://localhost/health > /dev/null; then
        echo -e "${GREEN}✓ Load balancer đang hoạt động${NC}"
    else
        echo -e "${RED}✗ Load balancer không phản hồi${NC}"
    fi
    
    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis đang hoạt động${NC}"
    else
        echo -e "${RED}✗ Redis không phản hồi${NC}"
    fi
}

# Performance testing
run_performance_test() {
    echo -e "${YELLOW}Chạy test hiệu suất...${NC}"
    
    # Install Apache Bench if not available
    if ! command -v ab &> /dev/null; then
        sudo apt install -y apache2-utils
    fi
    
    echo -e "${BLUE}Testing concurrent connections...${NC}"
    
    # Test health endpoint with concurrent requests
    ab -n 100 -c 10 http://localhost/health
    
    echo -e "${BLUE}Testing WebSocket connections...${NC}"
    
    # Create simple WebSocket test
    cat > test_websocket.js <<'EOF'
const WebSocket = require('ws');

const TEST_CONNECTIONS = 20;
const connections = [];

console.log(`Tạo ${TEST_CONNECTIONS} kết nối WebSocket...`);

for (let i = 0; i < TEST_CONNECTIONS; i++) {
    const ws = new WebSocket('ws://localhost/ws');
    
    ws.on('open', () => {
        console.log(`Kết nối ${i + 1} thành công`);
        
        // Send ping message
        ws.send(JSON.stringify({
            type: 'ping',
            connection_id: i + 1
        }));
    });
    
    ws.on('message', (data) => {
        const message = JSON.parse(data.toString());
        if (message.type === 'pong') {
            console.log(`Pong từ kết nối ${i + 1}`);
        }
    });
    
    ws.on('error', (error) => {
        console.error(`Lỗi kết nối ${i + 1}:`, error.message);
    });
    
    connections.push(ws);
}

// Close connections after 10 seconds
setTimeout(() => {
    connections.forEach(ws => ws.close());
    console.log('Đóng tất cả kết nối test');
    process.exit(0);
}, 10000);
EOF
    
    # Run WebSocket test if Node.js is available
    if command -v node &> /dev/null; then
        npm install ws
        node test_websocket.js
        rm test_websocket.js
    fi
}

# Monitor system performance
setup_monitoring() {
    echo -e "${YELLOW}Thiết lập monitoring...${NC}"
    
    # Create monitoring script
    cat > monitor_multiuser.sh <<'EOF'
#!/bin/bash

echo "=== Seed-VC CPU Multi-User System Monitor ==="
echo "Thời gian: $(date)"
echo

# System resources
echo "📊 TÀI NGUYÊN HỆ THỐNG:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free -m | awk 'NR==2{printf "%.1f%% (%d/%dMB)", $3*100/$2, $3, $2}')"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{print $5 " (" $3 "/" $2 ")"}')"
echo

# Service status
echo "🏃 TRẠNG THÁI SERVICES:"
for service in $(systemctl list-units --type=service | grep seed-vc- | awk '{print $1}'); do
    if systemctl is-active $service > /dev/null; then
        echo "✓ $service: RUNNING"
    else
        echo "✗ $service: STOPPED"
    fi
done
echo

# Network connections
echo "🌐 KẾT NỐI MẠNG:"
echo "Active connections: $(netstat -an | grep :80 | grep ESTABLISHED | wc -l)"
echo "WebSocket connections: $(netstat -an | grep :8000 | grep ESTABLISHED | wc -l)"
echo

# Redis stats
echo "💾 REDIS STATS:"
if command -v redis-cli &> /dev/null; then
    redis-cli info stats | grep -E "connected_clients|total_commands_processed|keyspace_hits|keyspace_misses"
fi
echo

# Process information
echo "⚡ TOP PROCESSES:"
ps aux --sort=-%cpu | head -10 | awk '{printf "%-20s %5s %5s %s\n", substr($11,1,20), $3"%", $4"%", $2}'
EOF
    
    chmod +x monitor_multiuser.sh
    
    # Setup log rotation for multiple instances
    sudo tee /etc/logrotate.d/seed-vc-multiuser > /dev/null <<EOF
$PWD/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    sharedscripts
    postrotate
        systemctl reload seed-vc-* || true
    endscript
}
EOF
}

# Main deployment function
main() {
    check_system_requirements
    
    case $DEPLOYMENT_MODE in
        "docker"|"production-docker")
            optimize_system
            deploy_docker_production
            ;;
        "systemd"|"production-systemd")
            optimize_system
            deploy_systemd_production
            ;;
        "performance-test")
            run_performance_test
            ;;
        *)
            echo -e "${RED}Chế độ deployment không hợp lệ: $DEPLOYMENT_MODE${NC}"
            echo "Sử dụng: $0 [docker|systemd|performance-test] [scale_factor] [max_concurrent_users]"
            exit 1
            ;;
    esac
    
    setup_monitoring
    
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  TRIỂN KHAI MULTI-USER HOÀN THÀNH!           ${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo
    echo -e "${YELLOW}🌐 URLs Truy Cập:${NC}"
    echo "Frontend: http://$(hostname -I | awk '{print $1}')"
    echo "API Health: http://$(hostname -I | awk '{print $1}')/health"
    if [ "$DEPLOYMENT_MODE" == "docker" ]; then
        echo "HAProxy Stats: http://$(hostname -I | awk '{print $1}'):8404"
        echo "Grafana Dashboard: http://$(hostname -I | awk '{print $1}'):3001"
    fi
    echo
    echo -e "${YELLOW}📊 Monitoring:${NC}"
    echo "Chạy: ./monitor_multiuser.sh"
    echo "Logs: tail -f logs/*.log"
    echo
    echo -e "${YELLOW}⚡ Khả Năng Xử Lý:${NC}"
    echo "Người dùng đồng thời: $MAX_CONCURRENT_USERS"
    echo "Backend instances: $SCALE_FACTOR"
    echo "Frontend instances: $SCALE_FACTOR"
    echo
    echo -e "${GREEN}Hệ thống sẵn sàng phục vụ nhiều người dùng cùng lúc! 🚀${NC}"
}

# Run main function
main