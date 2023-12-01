#!/bin/bash
set -e
cd /opt/star-burger/
systemctl stop nginx
mkdir -p nginx/letsencrypt/
cp -a /etc/letsencrypt/ /opt/star-burger/nginx/
chmod u+x entrypoint.prod.sh
docker compose up -d --build
sudo docker exec -i star-burger-django-1 python manage.py migrate --noiput
sudo docker exec -i star-burger-django-1 python manage.py loaddata data.json
printf "\nDeploy completed!\n"