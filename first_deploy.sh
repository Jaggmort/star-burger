#!/bin/bash
set -e
cd /opt/star-burger/
systemctl stop nginx
cp -a /etc/letsencrypt/ /opt/star-burger/ngingx/letsencrypt/
docker compose up -d --build
docker compose exec django python manage.py migrate --noinput
docker compose exec django python manage.py loaddata data.json
docker compose exec django python manage.py collectstatic --no-input 
printf "\nDeploy completed!\n"
