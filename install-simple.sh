#!/bin/bash

# Seed-VC CPU Simple Installation Script
# For Ubuntu 22.04 - Root User

set -e

echo "🚀 Seed-VC CPU - Cài Đặt Đơn Giản"
echo "=================================="

# Update system
echo "📦 Updating system..."
apt update && apt upgrade -y

# Install basic dependencies
echo "🔧 Installing dependencies..."
apt install -y \
    build-essential \
    curl \
    wget \
    git \
    ffmpeg \
    sox \
    libsox-fmt-all \
    libsndfile1-dev \
    python3.9 \
    python3.9-dev \
    python3.9-venv \
    python3-pip \
    redis-server \
    nginx \
    htop

# Install Node.js 18
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install pnpm globally
echo "📦 Installing pnpm..."
npm install -g pnpm

# Create seedvc user
echo "👤 Setting up user..."
if ! id "seedvc" &>/dev/null; then
    useradd -m -s /bin/bash seedvc
    usermod -aG sudo seedvc
fi

# Setup project
PROJECT_DIR="/home/seedvc/seed-vc-cpu"
echo "📁 Setting up project at $PROJECT_DIR..."

# Copy files
mkdir -p $PROJECT_DIR
cp -r . $PROJECT_DIR/
chown -R seedvc:seedvc $PROJECT_DIR

# Install dependencies as seedvc user
echo "📦 Installing Python dependencies..."
sudo -u seedvc bash -c "
    cd $PROJECT_DIR
    python3.9 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install fastapi uvicorn
    pip install soundfile librosa numpy scipy
    pip install aiofiles aioredis redis
    pip install websockets python-multipart
"

echo "📦 Installing Node.js dependencies..."
sudo -u seedvc bash -c "
    cd $PROJECT_DIR
    pnpm install
"

# Create simple start scripts
cat > $PROJECT_DIR/start-simple.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "🔨 Building frontend..."
pnpm run build --no-lint

echo "🚀 Starting services..."

# Start Redis
sudo systemctl start redis-server

# Start backend
source venv/bin/activate
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
echo $! > ../backend.pid
cd ..

# Start frontend  
pnpm start &
echo $! > frontend.pid

echo "✅ Services started!"
echo "🌐 Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "🔧 Backend API: http://$(hostname -I | awk '{print $1}'):8000"
echo "📊 Health: http://$(hostname -I | awk '{print $1}'):8000/health"
echo ""
echo "To stop: ./stop-simple.sh"
EOF

cat > $PROJECT_DIR/stop-simple.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "🛑 Stopping services..."

if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null || true
    rm backend.pid
fi

if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null || true
    rm frontend.pid
fi

pkill -f "uvicorn main:app" || true
pkill -f "pnpm start" || true

echo "✅ Services stopped!"
EOF

cat > $PROJECT_DIR/check-status.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "📊 Seed-VC CPU Status"
echo "===================="

# Check processes
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend: RUNNING (port 8000)"
else
    echo "❌ Backend: STOPPED"
fi

if pgrep -f "pnpm start" > /dev/null; then
    echo "✅ Frontend: RUNNING (port 3000)"
else
    echo "❌ Frontend: STOPPED"
fi

if systemctl is-active redis-server > /dev/null; then
    echo "✅ Redis: RUNNING"
else
    echo "❌ Redis: STOPPED"
fi

echo ""
echo "💻 System Resources:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free -m | awk 'NR==2{printf "%d/%dMB (%.1f%%)", $3,$2,$3*100/$2}')"
echo "Disk: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')"

echo ""
echo "🌐 Test URLs:"
echo "curl http://localhost:8000/health"
echo "curl http://localhost:3000"
EOF

# Make scripts executable
chmod +x $PROJECT_DIR/*.sh
chown seedvc:seedvc $PROJECT_DIR/*.sh

# Setup firewall
echo "🔒 Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp
ufw allow 8000/tcp
ufw --force enable

# Start Redis
systemctl start redis-server
systemctl enable redis-server

echo ""
echo "✅ Cài Đặt Hoàn Thành!"
echo "====================="
echo ""
echo "🎯 Next Steps:"
echo "1. su - seedvc"
echo "2. cd $PROJECT_DIR"
echo "3. ./start-simple.sh"
echo "4. ./check-status.sh"
echo ""
echo "🌐 URLs sau khi start:"
echo "Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "Backend: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "📝 Files created:"
echo "- start-simple.sh: Khởi động services"
echo "- stop-simple.sh: Dừng services"  
echo "- check-status.sh: Kiểm tra trạng thái"
echo ""
echo "🎉 Project ready at: $PROJECT_DIR"