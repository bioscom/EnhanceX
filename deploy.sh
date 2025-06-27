#!/bin/bash

# Define paths
PROJECT_DIR="/glb/home/ngibe6/enhancex"
VENV_DIR="$PROJECT_DIR/venv"
GUNICORN_SERVICE="gunicorn"

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Changing to project directory..."
cd "$PROJECT_DIR" || { echo "Failed to change directory to $PROJECT_DIR"; exit 1; }

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting Gunicorn via systemd..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl restart "$GUNICORN_SERVICE"

echo "Reloading Nginx..."
sudo systemctl reload nginx

echo "Deployment complete."
