#!/bin/bash
#
# ======================================================
# Lablr Development Environment Setup and Startup Script
# ======================================================
#
# This script automates the setup and startup of all components required
# for running the Lablr application:
#
# 1. Checks for and installs prerequisites
# 2. Creates a Python virtual environment
# 3. Installs backend dependencies
# 4. Starts PostgreSQL and Redis in Docker containers
# 5. Applies database migrations
# 6. Starts the FastAPI backend server
# 7. Starts the Celery worker
# 8. Installs frontend dependencies and starts the Next.js dev server
#
# Run this script from the project root directory to start the entire
# application stack with a single command.
#
# Usage: ./start_all.sh
#

set -e

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base directory (where this script is located)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}             LABLR STARTUP SCRIPT             ${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}Starting Lablr services...${NC}"

# Ensure .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: No .env file found. Creating from template...${NC}"
    if [ -f env.template ]; then
        cp env.template .env
        echo -e "${YELLOW}Created .env from template. Please update with your credentials!${NC}"
    else
        echo -e "${RED}Error: env.template not found. Creating a basic .env file...${NC}"
        cat > .env << EOF
# Basic configuration
DATABASE_URL=postgresql://lablr:lablr_dev_password@localhost:5432/lablr
REDIS_URL=redis://localhost:6379
SECRET_KEY=dev-secret-key-replace-in-production
EOF
    fi
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH. Please install Docker to continue.${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running. Please start Docker to continue.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose not found. Please install Docker Compose to continue.${NC}"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH. Please install Python 3 to continue.${NC}"
    exit 1
fi

# Set up Python virtual environment
echo -e "${GREEN}Setting up Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}Created virtual environment in .venv directory${NC}"
fi

# Source the virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start Docker services (PostgreSQL and Redis)
echo -e "${GREEN}Starting Docker services (PostgreSQL and Redis)...${NC}"
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo -e "${GREEN}Waiting for PostgreSQL to be ready...${NC}"
sleep 5

# Check if PostgreSQL is ready
echo -e "${GREEN}Checking PostgreSQL connection...${NC}"
RETRIES=10
while [ $RETRIES -gt 0 ]
do
    if python -c "import psycopg2; conn = psycopg2.connect('$(grep DATABASE_URL .env | cut -d'=' -f2-)')" &> /dev/null; then
        echo -e "${GREEN}PostgreSQL is up and running!${NC}"
        break
    fi
    RETRIES=$((RETRIES-1))
    echo -e "${YELLOW}Waiting for PostgreSQL... ${RETRIES} attempts left${NC}"
    sleep 3
done

if [ $RETRIES -eq 0 ]; then
    echo -e "${YELLOW}Warning: Could not connect to PostgreSQL, but continuing anyway...${NC}"
fi

# Apply database migrations
echo -e "${GREEN}Applying database migrations...${NC}"
alembic upgrade head

# Create upload directory if it doesn't exist
mkdir -p uploads

# Start the backend API server in the background
echo -e "${GREEN}Starting FastAPI backend server...${NC}"
uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload & 
BACKEND_PID=$!

# Start Celery worker in the background
echo -e "${GREEN}Starting Celery worker...${NC}"
celery -A src.workers.tasks worker --loglevel=info & 
CELERY_PID=$!

# Check if Node.js is installed
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}Warning: Node.js or npm not found. Frontend will not be started.${NC}"
    SKIP_FRONTEND=true
else
    SKIP_FRONTEND=false
fi

# Install and start frontend
if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${GREEN}Setting up frontend...${NC}"
    cd frontend
    
    # Install frontend dependencies
    echo -e "${GREEN}Installing frontend dependencies...${NC}"
    npm install --quiet
    
    # Start the frontend development server
    echo -e "${GREEN}Starting Next.js frontend...${NC}"
    npm run dev & 
    FRONTEND_PID=$!
    cd "$BASE_DIR"
else
    echo -e "${YELLOW}Skipping frontend startup due to missing Node.js/npm${NC}"
    FRONTEND_PID=""
fi

# Function to handle shutdown
cleanup() {
    echo -e "${GREEN}Shutting down services...${NC}"
    
    # Kill backend processes if they're running
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ -n "$CELERY_PID" ]; then
        kill $CELERY_PID 2>/dev/null || true
    fi
    
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Stop Docker containers
    echo -e "${GREEN}Stopping Docker containers...${NC}"
    docker-compose down
    
    echo -e "${GREEN}Deactivating virtual environment...${NC}"
    deactivate 2>/dev/null || true
    
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${GREEN}All services stopped. Thank you for using Lablr!${NC}"
    echo -e "${BLUE}===============================================${NC}"
    exit 0
}

# Trap signals and call cleanup
trap cleanup SIGINT SIGTERM EXIT

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}All services started successfully!${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Backend API: http://localhost:8001${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait indefinitely
wait
