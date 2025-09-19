#!/bin/bash

# Seed-VC CPU Setup Script for Ubuntu 22.04
# This script sets up the complete environment for voice conversion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="seed-vc-cpu"
PYTHON_VERSION="3.9"
NODE_VERSION="18"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Seed-VC CPU Setup Script      ${NC}"
echo -e "${BLUE}  Ubuntu 22.04 VPS Installation ${NC}"
echo -e "${BLUE}================================${NC}"

# Check if running as root and handle appropriately
if [[ $EUID -eq 0 ]]; then
   echo -e "${YELLOW}Running as root - will create non-root user for application${NC}"
   
   # Create seedvc user if not exists
   if ! id "seedvc" &>/dev/null; then
       echo -e "${YELLOW}Creating seedvc user...${NC}"
       useradd -m -s /bin/bash seedvc
       usermod -aG sudo seedvc
       echo "seedvc ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
   fi
   
   # Set up project directory
   PROJECT_DIR="/home/seedvc/seed-vc-cpu"
   mkdir -p $PROJECT_DIR
   
   # Copy project files to user directory
   if [ "$PWD" != "$PROJECT_DIR" ]; then
       echo -e "${YELLOW}Copying project files to $PROJECT_DIR...${NC}"
       cp -r . $PROJECT_DIR/
       chown -R seedvc:seedvc $PROJECT_DIR
   fi
   
   # Continue setup as seedvc user
   echo -e "${YELLOW}Continuing setup as seedvc user...${NC}"
   cd $PROJECT_DIR
   sudo -u seedvc bash "$0" "$@"
   exit $?
else
   echo -e "${GREEN}Running as user: $(whoami)${NC}"
   PROJECT_DIR="$HOME/seed-vc-cpu"
   
   # If not in project directory, create it
   if [ ! -f "package.json" ] && [ "$PWD" != "$PROJECT_DIR" ]; then
       mkdir -p $PROJECT_DIR
       cd $PROJECT_DIR
   fi
fi

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
if [[ $EUID -eq 0 ]]; then
    apt update && apt upgrade -y
else
    sudo apt update && sudo apt upgrade -y
fi

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
if [[ $EUID -eq 0 ]]; then
    APT_CMD="apt install -y"
else
    APT_CMD="sudo apt install -y"
fi

$APT_CMD \
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
    libffi-dev \
    liblzma-dev \
    pkg-config \
    nginx \
    htop \
    tree \
    redis-server

# Install Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    
    if [[ $EUID -eq 0 ]]; then
        sh get-docker.sh
        usermod -aG docker seedvc
    else
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
    fi
    
    rm get-docker.sh
    
    # Install Docker Compose
    if [[ $EUID -eq 0 ]]; then
        curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
else
    echo -e "${GREEN}Docker already installed${NC}"
fi

# Install Python 3.9 if not available
if ! command -v python3.9 &> /dev/null; then
    echo -e "${YELLOW}Installing Python 3.9...${NC}"
    if [[ $EUID -eq 0 ]]; then
        apt install -y software-properties-common
        add-apt-repository ppa:deadsnakes/ppa -y
        apt update
        apt install -y python3.9 python3.9-dev python3.9-venv python3-pip
    else
        sudo apt install -y software-properties-common
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt update
        sudo apt install -y python3.9 python3.9-dev python3.9-venv python3-pip
    fi
fi

# Install Node.js 18
if ! command -v node &> /dev/null || [[ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" -lt "18" ]]; then
    echo -e "${YELLOW}Installing Node.js 18...${NC}"
    if [[ $EUID -eq 0 ]]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt install -y nodejs
    else
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt install -y nodejs
    fi
fi

# Install pnpm
if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}Installing pnpm...${NC}"
    npm install -g pnpm
fi

# Create project directories
echo -e "${YELLOW}Creating project directories...${NC}"
if [[ $EUID -eq 0 ]]; then
    USER_HOME="/home/seedvc"
    PROJECT_DIR="$USER_HOME/seed-vc-cpu"
else
    USER_HOME="$HOME"
    PROJECT_DIR="$USER_HOME/seed-vc-cpu"
fi

mkdir -p $PROJECT_DIR/{uploads,outputs,models,logs,ssl}

# If we're not already in the project directory, copy files there
if [ "$PWD" != "$PROJECT_DIR" ] && [ -f "package.json" ]; then
    echo -e "${YELLOW}Copying project files to $PROJECT_DIR...${NC}"
    cp -r . $PROJECT_DIR/
    if [[ $EUID -eq 0 ]]; then
        chown -R seedvc:seedvc $PROJECT_DIR
    fi
fi

cd $PROJECT_DIR

# Setup Python virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
python3.9 -m venv venv
source venv/bin/activate

# Install Python dependencies
if [ -f "backend/requirements.txt" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r backend/requirements.txt
else
    echo -e "${RED}requirements.txt not found. Please copy project files first.${NC}"
fi

# Install Node.js dependencies
if [ -f "package.json" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    pnpm install
else
    echo -e "${RED}package.json not found. Please copy project files first.${NC}"
fi

# Generate SSL certificates for development
echo -e "${YELLOW}Generating SSL certificates for development...${NC}"
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Setup systemd services
echo -e "${YELLOW}Setting up systemd services...${NC}"

# Backend service
sudo tee /etc/systemd/system/seed-vc-backend.service > /dev/null <<EOF
[Unit]
Description=Seed-VC Backend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/seed-vc-cpu
Environment=PATH=$HOME/seed-vc-cpu/venv/bin
ExecStart=$HOME/seed-vc-cpu/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
sudo tee /etc/systemd/system/seed-vc-frontend.service > /dev/null <<EOF
[Unit]
Description=Seed-VC Frontend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/seed-vc-cpu
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/pnpm start
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
sudo cp nginx/nginx.conf /etc/nginx/sites-available/seed-vc-cpu
sudo ln -sf /etc/nginx/sites-available/seed-vc-cpu /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Create SSL directory for Nginx
sudo mkdir -p /etc/nginx/ssl
sudo cp ssl/cert.pem /etc/nginx/ssl/
sudo cp ssl/key.pem /etc/nginx/ssl/

# Test Nginx configuration
sudo nginx -t

# Setup log rotation
echo -e "${YELLOW}Setting up log rotation...${NC}"
sudo tee /etc/logrotate.d/seed-vc-cpu > /dev/null <<EOF
$HOME/seed-vc-cpu/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

# Setup firewall
echo -e "${YELLOW}Configuring firewall...${NC}"
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Create startup script
cat > start.sh <<'EOF'
#!/bin/bash

echo "Starting Seed-VC CPU services..."

# Start backend
sudo systemctl start seed-vc-backend
sudo systemctl enable seed-vc-backend

# Build and start frontend
pnpm run build
sudo systemctl start seed-vc-frontend
sudo systemctl enable seed-vc-frontend

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

echo "All services started!"
echo "Access the application at:"
echo "  HTTP:  http://$(hostname -I | awk '{print $1}')"
echo "  HTTPS: https://$(hostname -I | awk '{print $1}')"
EOF

chmod +x start.sh

# Create monitoring script
cat > monitor.sh <<'EOF'
#!/bin/bash

echo "=== Seed-VC CPU Service Status ==="
echo "Backend Service:"
sudo systemctl status seed-vc-backend --no-pager -l

echo -e "\nFrontend Service:"
sudo systemctl status seed-vc-frontend --no-pager -l

echo -e "\nNginx Service:"
sudo systemctl status nginx --no-pager -l

echo -e "\nSystem Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{print $5}')"

echo -e "\nPort Status:"
sudo netstat -tlnp | grep -E ":(80|443|3000|8000)"
EOF

chmod +x monitor.sh

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Setup Complete!               ${NC}"
echo -e "${GREEN}================================${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Copy your project files to ~/seed-vc-cpu/"
echo "2. Run './start.sh' to start all services"
echo "3. Use './monitor.sh' to check service status"
echo
echo -e "${YELLOW}Useful commands:${NC}"
echo "- View logs: journalctl -u seed-vc-backend -f"
echo "- Restart services: sudo systemctl restart seed-vc-backend"
echo "- Build frontend: pnpm run build"
echo
echo -e "${GREEN}The system is ready for Seed-VC CPU deployment!${NC}"

# Log out and back in to apply docker group membership
echo -e "${YELLOW}Please log out and back in to use Docker without sudo${NC}"