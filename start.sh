#!/usr/bin/env bash
# exit on error
set -o errexit

python manage.py migrate
python manage.py seed_demo_data
gunicorn core.wsgi:application
