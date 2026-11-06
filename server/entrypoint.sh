#!/bin/sh
set -eu
umask 077
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py collectstatic --noinput
exec "$@"
