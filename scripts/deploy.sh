#!/bin/bash

# Seed-VC CPU Deployment Script
# Builds and deploys the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_TYPE=${1:-"production"}
USE_DOCKER=${2:-"false"}

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Seed-VC CPU Deployment Script ${NC}"
echo -e "${BLUE}  Mode: $DEPLOYMENT_TYPE           ${NC}"
echo -e "${BLUE}================================${NC}"

# Check if in project directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found. Run from project root.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p uploads outputs models logs ssl

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
if [ "$DEPLOYMENT_TYPE" == "development" ]; then
    pnpm run build
else
    pnpm run build --no-lint
fi

# Install backend dependencies if virtual environment doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3.9 -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
else
    source venv/bin/activate
fi

# Run deployment based on type
if [ "$USE_DOCKER" == "true" ]; then
    deploy_with_docker
elif [ "$DEPLOYMENT_TYPE" == "development" ]; then
    deploy_development
else
    deploy_production
fi

function deploy_with_docker() {
    echo -e "${YELLOW}Deploying with Docker...${NC}"
    
    # Stop existing containers
    docker-compose down || true
    
    # Build and start containers
    docker-compose build
    docker-compose up -d
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 30
    
    # Check service health
    check_services_docker
}

function deploy_development() {
    echo -e "${YELLOW}Deploying in development mode...${NC}"
    
    # Kill existing processes
    pkill -f "uvicorn main:app" || true
    pkill -f "pnpm start" || true
    
    # Start backend in background
    echo -e "${YELLOW}Starting backend...${NC}"
    cd backend
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    cd ..
    
    # Wait for backend to start
    sleep 5
    
    # Start frontend in background
    echo -e "${YELLOW}Starting frontend...${NC}"
    nohup pnpm start > logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
    
    # Wait for services to be ready
    sleep 10
    
    check_services_local
}

function deploy_production() {
    echo -e "${YELLOW}Deploying in production mode...${NC}"
    
    # Stop services
    sudo systemctl stop seed-vc-frontend || true
    sudo systemctl stop seed-vc-backend || true
    sudo systemctl stop nginx || true
    
    # Install/update systemd services
    setup_systemd_services
    
    # Start services
    sudo systemctl start seed-vc-backend
    sudo systemctl enable seed-vc-backend
    sleep 5
    
    sudo systemctl start seed-vc-frontend
    sudo systemctl enable seed-vc-frontend
    sleep 5
    
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    # Check service status
    check_services_systemd
}

function setup_systemd_services() {
    echo -e "${YELLOW}Setting up systemd services...${NC}"
    
    # Backend service
    sudo tee /etc/systemd/system/seed-vc-backend.service > /dev/null <<EOF
[Unit]
Description=Seed-VC Backend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend
Restart=always
RestartSec=3
StandardOutput=append:$PWD/logs/backend.log
StandardError=append:$PWD/logs/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    sudo tee /etc/systemd/system/seed-vc-frontend.service > /dev/null <<EOF
[Unit]
Description=Seed-VC Frontend Service
After=network.target seed-vc-backend.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NEXT_PUBLIC_API_URL=http://localhost:8000
ExecStart=/usr/bin/pnpm start
Restart=always
RestartSec=3
StandardOutput=append:$PWD/logs/frontend.log
StandardError=append:$PWD/logs/frontend-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
}

function check_services_local() {
    echo -e "${YELLOW}Checking services...${NC}"
    
    # Check backend
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend is running${NC}"
    else
        echo -e "${RED}✗ Backend is not responding${NC}"
        cat logs/backend.log | tail -20
    fi
    
    # Check frontend
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✓ Frontend is running${NC}"
    else
        echo -e "${RED}✗ Frontend is not responding${NC}"
        cat logs/frontend.log | tail -20
    fi
}

function check_services_systemd() {
    echo -e "${YELLOW}Checking services...${NC}"
    
    # Check backend
    if sudo systemctl is-active seed-vc-backend > /dev/null; then
        echo -e "${GREEN}✓ Backend service is active${NC}"
    else
        echo -e "${RED}✗ Backend service failed${NC}"
        sudo systemctl status seed-vc-backend --no-pager -l
    fi
    
    # Check frontend
    if sudo systemctl is-active seed-vc-frontend > /dev/null; then
        echo -e "${GREEN}✓ Frontend service is active${NC}"
    else
        echo -e "${RED}✗ Frontend service failed${NC}"
        sudo systemctl status seed-vc-frontend --no-pager -l
    fi
    
    # Check nginx
    if sudo systemctl is-active nginx > /dev/null; then
        echo -e "${GREEN}✓ Nginx is active${NC}"
    else
        echo -e "${RED}✗ Nginx failed${NC}"
        sudo systemctl status nginx --no-pager -l
    fi
    
    # Test endpoints
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend API is responding${NC}"
    else
        echo -e "${RED}✗ Backend API is not responding${NC}"
    fi
}

function check_services_docker() {
    echo -e "${YELLOW}Checking Docker services...${NC}"
    
    # Check containers
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✓ Docker containers are running${NC}"
        docker-compose ps
    else
        echo -e "${RED}✗ Docker containers failed${NC}"
        docker-compose logs --tail=20
        exit 1
    fi
    
    # Check endpoints
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend API is responding${NC}"
    else
        echo -e "${RED}✗ Backend API is not responding${NC}"
        docker-compose logs backend --tail=20
    fi
    
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✓ Frontend is responding${NC}"
    else
        echo -e "${RED}✗ Frontend is not responding${NC}"
        docker-compose logs frontend --tail=20
    fi
}

# Run deployment
main() {
    case $USE_DOCKER in
        "true")
            deploy_with_docker
            ;;
        *)
            case $DEPLOYMENT_TYPE in
                "development")
                    deploy_development
                    ;;
                "production")
                    deploy_production
                    ;;
                *)
                    echo -e "${RED}Invalid deployment type: $DEPLOYMENT_TYPE${NC}"
                    echo "Usage: $0 [development|production] [true|false]"
                    exit 1
                    ;;
            esac
            ;;
    esac
    
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  Deployment Complete!          ${NC}"
    echo -e "${GREEN}================================${NC}"
    echo
    echo -e "${YELLOW}Application URLs:${NC}"
    echo "Frontend: http://localhost:3000"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8000/health"
    echo
    if [ "$DEPLOYMENT_TYPE" == "production" ]; then
        echo -e "${YELLOW}Management Commands:${NC}"
        echo "View logs: journalctl -u seed-vc-backend -f"
        echo "Restart backend: sudo systemctl restart seed-vc-backend"
        echo "Restart frontend: sudo systemctl restart seed-vc-frontend"
        echo "Monitor services: ./monitor.sh"
    fi
    echo
    echo -e "${GREEN}Deployment successful!${NC}"
}

# Run main function
main