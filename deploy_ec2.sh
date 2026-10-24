#!/bin/bash
set -e

echo "=== 1. Updating System & Installing Dependencies ==="
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git curl nginx

# Install Node.js (v20 LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 process manager
sudo npm install -g pm2

echo "=== 2. Setting up Backend (Hermes) ==="
cd ~/
if [ ! -d "Hermes-trading" ]; then
    git clone https://github.com/Mahesh-Paul/Hermes-trading.git
fi
cd Hermes-trading
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Start backend using PM2
pm2 start "venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000" --name "hermes-api"

echo "=== 3. Setting up Frontend ==="
cd ~/
if [ ! -d "hermes-frontend" ]; then
    git clone https://github.com/Mahesh-Paul/hermes-frontend.git
fi
cd hermes-frontend
npm install
npm run build

# Start frontend using PM2 serve
sudo npm install -g serve
pm2 start "serve -s build -l 3000" --name "hermes-frontend"

pm2 save
pm2 startup

echo "=== Deployment Complete! ==="
echo "Backend:  http://<YOUR_EC2_PUBLIC_IP>:8000"
echo "Frontend: http://<YOUR_EC2_PUBLIC_IP>:3000"
