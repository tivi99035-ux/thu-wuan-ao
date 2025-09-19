# 📦 Tải Về Hệ Thống Seed-VC CPU Multi-User

## 🔗 Link Tải Về
```
https://bashupload.com/_wwPK/68iD0.zip
```

## 🔐 Mật Khẩu Giải Nén
```
369852
```

## 📋 Thông Tin File

- **Tên File**: `seed-vc-cpu-multiuser.zip`
- **Kích Thước**: 206KB (đã nén)
- **Bảo Mật**: Có mật khẩu bảo vệ
- **Nội Dung**: Hệ thống hoàn chỉnh với tất cả source code

## 🚀 Sau Khi Tải Về

### Bước 1: Giải Nén
```bash
# Tải về
wget https://bashupload.com/_wwPK/68iD0.zip

# Giải nén với mật khẩu
unzip -P 369852 68iD0.zip
cd seed-vc-cpu-multiuser/
```

### Bước 2: Triển Khai Cơ Bản
```bash
# Cài đặt dependencies
chmod +x scripts/setup.sh
./scripts/setup.sh

# Triển khai basic
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

### Bước 3: Triển Khai Multi-User (Khuyến nghị)
```bash
# Triển khai cho 50 người dùng đồng thời
chmod +x scripts/deploy-multiuser.sh
./scripts/deploy-multiuser.sh docker 3 50

# Hoặc cho 100+ người dùng
./scripts/deploy-multiuser.sh docker 4 100
```

## 📊 Cấu Hình Khuyến Nghị

| Số Người Dùng | CPU | RAM | Lệnh Triển Khai |
|----------------|-----|-----|-----------------|
| 10-20 | 4 cores | 8GB | `./scripts/deploy-multiuser.sh systemd 2 20` |
| 30-50 | 8 cores | 16GB | `./scripts/deploy-multiuser.sh docker 3 50` |
| 50-100 | 16 cores | 32GB | `./scripts/deploy-multiuser.sh docker 4 100` |
| 100+ | 32+ cores | 64GB+ | `./scripts/deploy-multiuser.sh docker 6 200` |

## 🔧 Tính Năng Chính

✅ **Chuyển Đổi Giọng Nói**: Multiple models (Base, Fast, Hi-Fi)
✅ **Nhân Bản Giọng Nói AI**: Clone giọng từ reference audio
✅ **Multi-User Support**: 50-100+ người dùng đồng thời
✅ **Real-time Updates**: WebSocket cho progress tracking
✅ **Load Balancing**: HAProxy + Multiple instances
✅ **Monitoring**: System dashboard với metrics
✅ **100% Tiếng Việt**: Toàn bộ giao diện
✅ **Docker Support**: Production clustering
✅ **Security**: Rate limiting + Resource isolation

## 📚 Documentation

- `README.md`: Hướng dẫn cơ bản
- `MULTI_USER_GUIDE.md`: Chi tiết multi-user deployment
- `TODO.md`: Implementation progress
- `scripts/`: Automated deployment scripts

## 🆘 Hỗ Trợ

Nếu gặp vấn đề:
1. Đọc `MULTI_USER_GUIDE.md` cho troubleshooting
2. Kiểm tra `logs/` directory cho error messages  
3. Sử dụng `./monitor_multiuser.sh` để check status

## ⚡ Quick Start

```bash
# Download và setup nhanh
wget https://bashupload.com/_wwPK/68iD0.zip
unzip -P 369852 68iD0.zip
cd seed-vc-cpu-multiuser/
./scripts/setup.sh
./scripts/deploy-multiuser.sh docker 3 50
```

Hệ thống sẽ chạy tại: `http://your-vps-ip` 🎉