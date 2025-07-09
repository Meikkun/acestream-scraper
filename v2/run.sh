#!/bin/bash

# Script to build and run Acestream Scraper v2
echo "=== Building and running Acestream Scraper v2 ==="

# Navigate to project root
cd $(dirname "$0")

# Check if we're in v2 directory
if [ ! -d "./frontend" ] || [ ! -d "./backend" ]; then
  echo "Error: This script must be run from the v2 directory."
  exit 1
fi

# Build frontend
echo "=== Building frontend ==="
cd frontend
npm install
npm run build:backend
if [ $? -ne 0 ]; then
  echo "Error: Frontend build failed."
  exit 1
fi

# Navigate to backend
cd ../backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "=== Creating Python virtual environment ==="
  python -m venv venv
fi

# Activate virtual environment
echo "=== Activating virtual environment ==="
source venv/bin/activate

# Install backend dependencies
echo "=== Installing backend dependencies ==="
pip install -r requirements.txt
if [ $? -ne 0 ]; then
  echo "Error: Failed to install backend dependencies."
  exit 1
fi

# Run the application
echo "=== Starting the application ==="
echo "The application will be available at http://localhost:8000"
echo "Press Ctrl+C to stop the server."
python main.py

# Deactivate virtual environment on exit
deactivate
