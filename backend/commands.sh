#!/bin/bash

python manage.py migrate
mkdir -p /app/collected_static
python manage.py collectstatic
mkdir -p /backend_static/static/
cp -r /app/collected_static/. /backend_static/static/
gunicorn --bind 0.0.0.0:80 backend.wsgi
exec "$@"
