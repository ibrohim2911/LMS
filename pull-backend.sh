#!/bin/bash

# Navigate to the directory of the script (project root)
cd "$(dirname "$0")"

echo "--- Pulling latest code ---"
git pull origin main

echo "--- Installing dependencies ---"
# Using install first ensures the environment exists
pipenv install

echo "--- Running Migrations ---"
pipenv run python manage.py makemigrations
pipenv run python manage.py migrate

echo "--- Create Superuser (Interactive) ---"
pipenv run python manage.py createsuperuser

echo "--- Starting Server ---"
pipenv run python manage.py runserver 0.0.0.0:8000
