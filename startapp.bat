cd C:\Users\User\Desktop\lms\project-library
start npm run dev

cd ..

start pipenv run python manage.py runserver 0.0.0.0:8000
start pipenv run celery -A config worker --pool=solo -l info
start pipenv run celery -A config beat -l info