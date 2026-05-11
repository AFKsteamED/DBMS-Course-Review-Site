release: python manage.py migrate
web: gunicorn course_review.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 60
