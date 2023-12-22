#!/usr/bin/env bash

set -e

function main() {
  python manage.py collectstatic --noinput
  export RUN_MAIN="true"
  if [ "$USE_GUNICORN" == "true" ]
  then
    echo "Starting with gunicorn..."
    gunicorn -c gunicorn_config.py server.wsgi:application --preload
  else
    echo "Starting with django..."
    python manage.py runserver 0.0.0.0:8000
  fi
}

main