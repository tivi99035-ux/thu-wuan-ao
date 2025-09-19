# Seed-VC CPU - Hệ Thống Chuyển Đổi Giọng Nói

Hệ thống chuyển đổi giọng nói tối ưu hóa CPU dựa trên Seed-VC, được thiết kế để triển khai trên Ubuntu 22.04 VPS không cần GPU. Bản triển khai này cung cấp giao diện web hoàn chỉnh cho chuyển đổi giọng nói thời gian thực với hỗ trợ nhiều mô hình và giọng nói.

## Tính Năng

- **Xử Lý Tối Ưu CPU**: Chuyển đổi giọng nói hiệu quả sử dụng ONNX Runtime và mô hình tối ưu CPU
- **Giao Diện Web Hiện Đại**: Frontend React/Next.js với xử lý âm thanh thời gian thực
- **Hỗ Trợ Nhiều Mô Hình**: Hỗ trợ các biến thể mô hình Seed-VC khác nhau (Cơ bản, Nhanh, Chất lượng cao)
- **Xử Lý Âm Thanh Thời Gian Thực**: Tải lên, ghi âm và chuyển đổi âm thanh với theo dõi tiến trình trực tiếp
- **Quản Lý Hàng Đợi**: Xử lý nền với hàng đợi công việc và giám sát trạng thái
- **Hỗ Trợ Docker**: Triển khai container hoàn chỉnh với Docker Compose
- **Sẵn Sàng Sản Xuất**: Nginx reverse proxy, hỗ trợ SSL và quản lý dịch vụ systemd

## Yêu Cầu Hệ Thống

### Yêu Cầu Tối Thiểu
- **Hệ Điều Hành**: Ubuntu 22.04 LTS
- **CPU**: 4+ nhân (Intel/AMD x64)
- **RAM**: 8GB tối thiểu (khuyến nghị 16GB)
- **Lưu Trữ**: 50GB dung lượng khả dụng
- **Mạng**: Kết nối internet băng rộng

### Yêu Cầu Khuyến Nghị (Multi-User)
- **CPU**: 8+ nhân với hỗ trợ AVX2 (16+ nhân cho 100+ người dùng)
- **RAM**: 16-32GB (64GB cho high-load)
- **Lưu Trữ**: SSD 100GB+ (500GB+ cho production)
- **Mạng**: Kết nối 100+ Mbps (1Gbps cho high-traffic)

### Khả Năng Xử Lý
| Cấu Hình | Người Dùng Đồng Thời | CPU | RAM | Ghi Chú |
|-----------|----------------------|-----|-----|---------|
| Cơ Bản    | 10-20 người          | 4 nhân | 8GB | Demo/Test |
| Tiêu Chuẩn | 30-50 người         | 8 nhân | 16GB | Small business |
| Cao Cấp   | 50-100 người         | 16 nhân | 32GB | Medium scale |
| Enterprise | 100+ người          | 32 nhân | 64GB | Large scale |

## Cài Đặt Nhanh

### Tùy Chọn 1: Multi-User Production (Khuyến nghị cho VPS)

```bash
# Clone repository
git clone https://github.com/yourusername/seed-vc-cpu.git
cd seed-vc-cpu

# Cài đặt tự động cho đa người dùng
chmod +x scripts/setup.sh
./scripts/setup.sh

# Triển khai multi-user (hỗ trợ 50+ người dùng đồng thời)
chmod +x scripts/deploy-multiuser.sh
./scripts/deploy-multiuser.sh docker 3 100
```

### Tùy Chọn 2: Docker Production với Load Balancing

```bash
# Clone và build với Docker Production
git clone https://github.com/yourusername/seed-vc-cpu.git
cd seed-vc-cpu

# Khởi động cluster production
docker-compose -f docker-compose.production.yml up -d

# Kiểm tra trạng thái cluster
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs
```

### Tùy Chọn 3: Cài Đặt Đơn Giản (Demo/Development)

```bash
# Cài đặt cơ bản
./scripts/deploy.sh production
```

### Option 3: Manual Installation

See [Manual Installation Guide](#manual-installation) below.

## Usage

Once deployed, access the web interface at:
- **HTTP**: `http://your-server-ip:3000`
- **HTTPS**: `https://your-server-ip` (with SSL configured)

### Basic Workflow

1. **Upload Audio**: Drag and drop audio files (WAV, MP3, FLAC, M4A) or record directly
2. **Select Model**: Choose from available voice conversion models
3. **Choose Target Speaker**: Select target voice characteristics
4. **Adjust Settings**: Fine-tune conversion strength, pitch preservation, and noise reduction
5. **Convert**: Start the conversion process with real-time progress tracking
6. **Download Results**: Play, compare, and download the converted audio

### Supported Audio Formats

- **Input**: WAV, MP3, FLAC, M4A (up to 100MB)
- **Output**: WAV (22.05 kHz, mono/stereo)
- **Quality**: 16-bit/24-bit depth support

## Architecture

### Frontend (Next.js)
- **Framework**: Next.js 15 with TypeScript
- **UI**: shadcn/ui components with Tailwind CSS
- **Audio**: WebAudio API for recording and playback
- **Real-time**: WebSocket integration for live updates

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Processing**: CPU-optimized audio processing pipeline
- **Models**: ONNX Runtime for efficient inference
- **Queue**: Background task processing with priority queues

### Infrastructure
- **Reverse Proxy**: Nginx with rate limiting and caching
- **Process Management**: systemd services for production
- **SSL**: Let's Encrypt integration ready
- **Monitoring**: Built-in health checks and logging

## API Documentation

### Core Endpoints

```bash
# Health check
GET /health

# List available models
GET /api/models

# Start voice conversion
POST /api/convert
Content-Type: multipart/form-data
- audio_file: File
- model_id: str
- target_speaker: str
- conversion_strength: float (0.0-1.0)
- preserve_pitch: float (0.0-1.0)
- noise_reduction: float (0.0-1.0)

# Check conversion status
GET /api/convert/{job_id}/status

# Download result
GET /api/convert/{job_id}/result
```

### Example API Usage

```bash
# Upload and convert audio
curl -X POST "http://localhost:8000/api/convert" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@input.wav" \
  -F "model_id=seed-vc-fast" \
  -F "target_speaker=speaker_001" \
  -F "conversion_strength=0.8"

# Response: {"job_id": "uuid-here", "status": "queued"}

# Check status
curl "http://localhost:8000/api/convert/{job_id}/status"

# Download result
curl "http://localhost:8000/api/convert/{job_id}/result" -o converted.wav
```

## Manual Installation

### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system packages
sudo apt install -y \
  build-essential curl wget git \
  ffmpeg sox libsox-fmt-all \
  libsndfile1-dev python3.9 python3.9-dev python3.9-venv \
  nodejs npm nginx

# Install pnpm
npm install -g pnpm
```

### 2. Application Setup

```bash
# Clone repository
git clone https://github.com/yourusername/seed-vc-cpu.git
cd seed-vc-cpu

# Install frontend dependencies
pnpm install

# Setup Python environment
python3.9 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Create directories
mkdir -p uploads outputs models logs ssl
```

### 3. Build and Deploy

```bash
# Build frontend
pnpm run build

# Start backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start frontend
cd ..
pnpm start &

# Configure Nginx (see nginx/nginx.conf)
sudo cp nginx/nginx.conf /etc/nginx/sites-available/seed-vc-cpu
sudo ln -s /etc/nginx/sites-available/seed-vc-cpu /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## Configuration

### Environment Variables

Create `.env` files for configuration:

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAX_FILE_SIZE=104857600

# Backend (.env)
LOG_LEVEL=INFO
MAX_WORKERS=2
MAX_QUEUE_SIZE=100
MODELS_DIR=./models
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
```

### Model Configuration

Models are automatically downloaded when first used. To pre-download:

```bash
# Download all models
python backend/download_models.py

# Or download specific model
curl -X POST "http://localhost:8000/api/models/seed-vc-fast/download"
```

## Monitoring and Maintenance

### Service Management

```bash
# Check service status
sudo systemctl status seed-vc-backend
sudo systemctl status seed-vc-frontend
sudo systemctl status nginx

# View logs
journalctl -u seed-vc-backend -f
journalctl -u seed-vc-frontend -f

# Restart services
sudo systemctl restart seed-vc-backend
sudo systemctl restart seed-vc-frontend
```

### Performance Monitoring

```bash
# Use built-in monitoring script
./scripts/monitor.sh

# Check system resources
htop
df -h
free -m

# Monitor API performance
curl http://localhost:8000/health
curl http://localhost:8000/queue/status
```

### Log Files

```
logs/
├── backend.log          # Backend application logs
├── frontend.log         # Frontend application logs
├── nginx-access.log     # Nginx access logs
└── nginx-error.log      # Nginx error logs
```

## Optimization

### CPU Performance

1. **Model Selection**: Use `seed-vc-fast` for best CPU performance
2. **Thread Configuration**: Adjust `MAX_WORKERS` based on CPU cores
3. **Memory Management**: Monitor RAM usage and adjust queue size
4. **Process Prioritization**: Use `nice` and `ionice` for background processing

### Audio Quality vs Speed

| Model | Quality | Speed | RAM Usage | Best For |
|-------|---------|-------|-----------|----------|
| seed-vc-fast | Good | Fast | 2-4GB | Real-time processing |
| seed-vc-base | Better | Medium | 4-8GB | Balanced quality/speed |
| seed-vc-hifi | Best | Slow | 8-16GB | Highest quality output |

## Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python dependencies
source venv/bin/activate
pip install -r backend/requirements.txt

# Check logs
tail -f logs/backend.log

# Test directly
cd backend && python -c "import main; print('OK')"
```

#### Frontend Build Fails
```bash
# Clear cache and reinstall
pnpm store prune
rm -rf node_modules
pnpm install

# Check Node.js version
node --version  # Should be 18+
```

#### Audio Processing Errors
```bash
# Check audio libraries
python -c "import soundfile, librosa; print('Audio libraries OK')"

# Test ffmpeg
ffmpeg -version

# Check file permissions
ls -la uploads/ outputs/
```

#### High CPU Usage
```bash
# Check running processes
htop
ps aux | grep -E "(uvicorn|node)"

# Reduce worker count
# Edit backend configuration: MAX_WORKERS=1
```

### Performance Issues

1. **Slow Conversion**: Reduce model size or lower quality settings
2. **Memory Errors**: Increase swap space or reduce queue size  
3. **Network Issues**: Check firewall and port configuration
4. **SSL Problems**: Verify certificate configuration

## Development

### Local Development

```bash
# Start backend in development mode
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start frontend in development mode
pnpm run dev

# Run tests
pnpm test
python -m pytest backend/tests/
```

### Adding New Models

1. Add model configuration to `backend/model_manager.py`
2. Update model download URLs
3. Test model loading and inference
4. Update frontend model selection UI

### Custom Speaker Training

For custom speaker models:
1. Prepare training data (clean audio samples)
2. Follow Seed-VC training procedures
3. Convert to ONNX format for CPU optimization
4. Add to model manager configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Seed-VC](https://github.com/Plachta/Seed-VC) - Original voice conversion implementation
- [ONNX Runtime](https://onnxruntime.ai/) - CPU-optimized inference engine
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - React framework for production

## Support

For issues and questions:
- Open an [issue](https://github.com/yourusername/seed-vc-cpu/issues)
- Check [troubleshooting guide](#troubleshooting)
- Review [API documentation](#api-documentation)

## Changelog

### v1.0.0
- Initial release with CPU optimization
- Complete web interface implementation
- Docker and systemd deployment support
- Multi-model support with automatic downloading
- Real-time processing with queue management
