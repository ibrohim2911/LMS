#!/bin/bash

# Navigate to the directory of the script (project root)
cd "$(dirname "$0")"

# Function to handle script exit ensures child processes are killed
cleanup() {
    echo "Stopping all services..."
    kill 0
}

# Trap SIGINT (Ctrl+C) to run cleanup
trap cleanup SIGINT


# Start Backend Server
echo "Starting Backend Server..."
pipenv run python manage.py runserver 0.0.0.0:8000 &

# Start Celery Worker
echo "Starting Celery Worker..."
# Note: --pool=solo is often used on Windows. On Linux, the default (prefork) is usually fine.
pipenv run celery -A config worker -l info &

# Start Celery Beat
echo "Starting Celery Beat..."
pipenv run celery -A config beat -l info &

# Wait for all background processes to finish
wait
