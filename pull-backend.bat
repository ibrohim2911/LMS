@echo off
cd /d "C:\Users\User\Desktop\lms"

echo --- Pulling latest code ---
git pull origin main

echo --- Installing dependencies ---
:: Using install first ensures the environment exists
call pipenv install

echo --- Running Migrations ---
call pipenv run python manage.py makemigrations
call pipenv run python manage.py migrate

echo --- Starting Server ---
:: Note: createsuperuser is interactive, so the script will wait for your input here
call pipenv run python manage.py createsuperuser

call pipenv run python manage.py runserver 0.0.0.0:8000

pause