#!/bin/bash

# Seed-VC CPU Setup Script for Root User
# Ubuntu 22.04 VPS Installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Seed-VC CPU Setup (Root)      ${NC}"
echo -e "${BLUE}  Ubuntu 22.04 VPS Installation ${NC}"
echo -e "${BLUE}================================${NC}"

# Create seedvc user
echo -e "${YELLOW}Creating seedvc user...${NC}"
if ! id "seedvc" &>/dev/null; then
    useradd -m -s /bin/bash seedvc
    usermod -aG sudo seedvc
    echo "seedvc ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
    echo -e "${GREEN}✓ Created seedvc user${NC}"
else
    echo -e "${GREEN}✓ seedvc user already exists${NC}"
fi

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
apt update && apt upgrade -y

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt install -y \
    build-essential \
    curl \
    wget \
    git \
    ffmpeg \
    sox \
    libsox-fmt-all \
    libsndfile1-dev \
    libffi-dev \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    pkg-config \
    nginx \
    htop \
    tree \
    redis-server \
    software-properties-common

# Install Python 3.9
echo -e "${YELLOW}Installing Python 3.9...${NC}"
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.9 python3.9-dev python3.9-venv python3-pip

# Install Node.js 18
echo -e "${YELLOW}Installing Node.js 18...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install pnpm
echo -e "${YELLOW}Installing pnpm...${NC}"
npm install -g pnpm

# Install Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker seedvc
    rm get-docker.sh
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}Docker already installed${NC}"
fi

# Setup project directory
PROJECT_DIR="/home/seedvc/seed-vc-cpu"
echo -e "${YELLOW}Setting up project directory: $PROJECT_DIR${NC}"

mkdir -p $PROJECT_DIR
cp -r . $PROJECT_DIR/ 2>/dev/null || true
chown -R seedvc:seedvc $PROJECT_DIR

# Setup Python virtual environment as seedvc user
echo -e "${YELLOW}Setting up Python environment...${NC}"
sudo -u seedvc bash -c "
    cd $PROJECT_DIR
    python3.9 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    if [ -f 'backend/requirements.txt' ]; then
        pip install -r backend/requirements.txt
    fi
"

# Install Node.js dependencies as seedvc user
echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
sudo -u seedvc bash -c "
    cd $PROJECT_DIR
    pnpm install
"

# Generate SSL certificates
echo -e "${YELLOW}Generating SSL certificates...${NC}"
mkdir -p $PROJECT_DIR/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout $PROJECT_DIR/ssl/key.pem \
    -out $PROJECT_DIR/ssl/cert.pem \
    -subj "/C=VN/ST=Vietnam/L=HoChiMinh/O=SeedVC/CN=localhost"

chown -R seedvc:seedvc $PROJECT_DIR/ssl

# Configure firewall
echo -e "${YELLOW}Configuring firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp
ufw allow 8000/tcp
ufw --force enable

# Start and enable Redis
echo -e "${YELLOW}Starting Redis...${NC}"
systemctl start redis-server
systemctl enable redis-server

# Create helpful scripts
echo -e "${YELLOW}Creating management scripts...${NC}"

# Build script
cat > $PROJECT_DIR/build.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "🔨 Building Seed-VC CPU..."
pnpm run build --no-lint
echo "✅ Build completed!"
EOF

# Start script
cat > $PROJECT_DIR/start.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting Seed-VC CPU..."

# Start backend
source venv/bin/activate
cd backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
echo $! > ../backend.pid
cd ..

# Start frontend
nohup pnpm start > logs/frontend.log 2>&1 &
echo $! > frontend.pid

echo "✅ Services started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "Logs: tail -f logs/*.log"
EOF

# Stop script
cat > $PROJECT_DIR/stop.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "🛑 Stopping Seed-VC CPU..."

# Stop processes
if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null || true
    rm backend.pid
fi

if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null || true
    rm frontend.pid
fi

# Kill by process name as backup
pkill -f "uvicorn main:app" || true
pkill -f "pnpm start" || true

echo "✅ Services stopped!"
EOF

# Status script
cat > $PROJECT_DIR/status.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "📊 Seed-VC CPU Status:"
echo

# Check processes
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend: RUNNING (PID: $(pgrep -f 'uvicorn main:app'))"
else
    echo "❌ Backend: STOPPED"
fi

if pgrep -f "pnpm start" > /dev/null; then
    echo "✅ Frontend: RUNNING (PID: $(pgrep -f 'pnpm start'))"
else
    echo "❌ Frontend: STOPPED"
fi

# Check ports
echo
echo "🌐 Network Status:"
netstat -tlnp 2>/dev/null | grep -E ":(3000|8000|6379)" || echo "No services listening"

# System resources
echo
echo "💻 System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free -m | awk 'NR==2{printf "%d/%dMB (%.1f%%)", $3,$2,$3*100/$2 }')"
echo "Disk: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')"
EOF

# Make scripts executable
chmod +x $PROJECT_DIR/*.sh
chown seedvc:seedvc $PROJECT_DIR/*.sh

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Setup Complete!               ${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo -e "${YELLOW}Next steps (as seedvc user):${NC}"
echo "1. Switch to seedvc user: su - seedvc"
echo "2. Go to project: cd $PROJECT_DIR"
echo "3. Build project: ./build.sh"
echo "4. Start services: ./start.sh"
echo "5. Check status: ./status.sh"
echo
echo -e "${YELLOW}Or run multi-user deployment:${NC}"
echo "su - seedvc"
echo "cd $PROJECT_DIR"
echo "./scripts/deploy-multiuser.sh docker 3 50"
echo
echo -e "${GREEN}Project ready at: $PROJECT_DIR${NC}"
echo -e "${GREEN}User: seedvc (password not set - use sudo)${NC}"