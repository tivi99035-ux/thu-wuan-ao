# 🚀 Hướng Dẫn Cài Đặt Nhanh - Seed-VC CPU Multi-User

## 🔧 Giải Quyết Lỗi "This script should not be run as root"

### ❌ Lỗi Gặp Phải
```bash
root@server:~/thu-wuan-ao# ./scripts/setup.sh
This script should not be run as root
```

### ✅ Giải Pháp: Sử dụng Script Root

**Bước 1: Sử dụng script setup dành cho root**
```bash
# Thay vì chạy scripts/setup.sh, chạy:
chmod +x setup-root.sh
./setup-root.sh
```

**Bước 2: Chuyển sang user seedvc**
```bash
# Sau khi setup xong, chuyển sang user seedvc
su - seedvc
cd /home/seedvc/seed-vc-cpu
```

**Bước 3: Build và khởi động**
```bash
# Build project
./build.sh

# Khởi động services
./start.sh

# Kiểm tra trạng thái
./status.sh
```

## 🏗️ Deployment Options

### Option 1: Cài Đặt Cơ Bản (1 user)
```bash
# Từ thư mục project
./build.sh
./start.sh

# Truy cập: http://your-vps-ip:3000
```

### Option 2: Multi-User Production (50+ users)
```bash
# Triển khai Docker multi-user
chmod +x scripts/deploy-multiuser.sh
./scripts/deploy-multiuser.sh docker 3 50

# Truy cập: http://your-vps-ip
```

### Option 3: Systemd Production
```bash
# Triển khai với systemd
./scripts/deploy-multiuser.sh systemd 2 30

# Services sẽ tự động khởi động
```

## 🎯 Commands Hữu Ích

### Quản Lý Services
```bash
# Khởi động
./start.sh

# Dừng
./stop.sh

# Kiểm tra trạng thái
./status.sh

# Xem logs
tail -f logs/*.log
```

### Debugging
```bash
# Kiểm tra ports
netstat -tlnp | grep -E ":(3000|8000|6379)"

# Kiểm tra processes
ps aux | grep -E "(uvicorn|pnpm|redis)"

# Test backend API
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

### Performance Monitoring
```bash
# System resources
htop

# Disk usage
df -h

# Memory usage
free -m

# Network connections
ss -tuln
```

## ⚡ Quick Commands Reference

```bash
# 🔄 SETUP (AS ROOT)
chmod +x setup-root.sh && ./setup-root.sh

# 👤 SWITCH USER
su - seedvc
cd /home/seedvc/seed-vc-cpu

# 🔨 BUILD
./build.sh

# 🚀 START BASIC
./start.sh

# 🏗️ START MULTI-USER (50 users)
./scripts/deploy-multiuser.sh docker 3 50

# 📊 CHECK STATUS
./status.sh

# 🛑 STOP
./stop.sh
```

## 🌐 Access URLs

Sau khi cài đặt thành công:

- **Frontend**: http://your-vps-ip:3000 (basic) hoặc http://your-vps-ip (multi-user)
- **Backend API**: http://your-vps-ip:8000
- **API Docs**: http://your-vps-ip:8000/docs
- **Health Check**: http://your-vps-ip:8000/health

## 🎊 Kết Quả Mong Đợi

Sau khi chạy thành công:
```bash
seedvc@server:~/seed-vc-cpu$ ./status.sh
📊 Seed-VC CPU Status:

✅ Backend: RUNNING (PID: 1234)
✅ Frontend: RUNNING (PID: 1235)

🌐 Network Status:
tcp 0.0.0.0:3000 LISTEN 1235/node
tcp 0.0.0.0:8000 LISTEN 1234/python

💻 System Resources:
CPU Usage: 15.2%
Memory: 2048/4096MB (50.0%)
Disk: 5.2G/25G (21%)
```

## 🆘 Troubleshooting

### Lỗi Permission
```bash
# Fix ownership
sudo chown -R seedvc:seedvc /home/seedvc/seed-vc-cpu
```

### Port đã sử dụng
```bash
# Kill existing processes
sudo pkill -f "uvicorn main:app"
sudo pkill -f "pnpm start"
```

### Dependencies missing
```bash
# Reinstall dependencies
cd /home/seedvc/seed-vc-cpu
source venv/bin/activate
pip install -r backend/requirements.txt
pnpm install
```

Hệ thống sẵn sàng hoạt động! 🎉