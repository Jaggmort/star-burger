#!/bin/bash
set -e
cd /opt/star-burger/
docker compose down
systemctl stop nginx
docker compose up -d --build
docker compose exec django python manage.py migrate --noinput
docker compose exec django python manage.py collectstatic --no-input 
printf "\nDeploy completed!\n"
