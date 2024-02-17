#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/starburger/
git pull git@github.com:Jaggmort/star-burger.git master
python3 -m venv .venv
npm ci --dev
./frontend/node_modules/.bin/parcel bundles-src/index.js --dist-dir bundles --public-url="./"
cd /opt/starburger/backend/
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
deactivate
cd /opt/starburger
systemctl reload nginx
systemctl restart starburger
set -o allexport && source .env && set +o allexport
curl https://api.rollbar.com/api/1/deploy/ \
  -F access_token=$ROLLBAR_ACCESS_TOKEN \
  -F environment=$ENVIROMENT  \
  -F revision=$(git rev-parse --verify HEAD) \
  -F local_username='Jaggmort'
