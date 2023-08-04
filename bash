#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/starburger/
git pull git@github.com:Jaggmort/star-burger.git master
python3 -m venv .venv
npm ci --dev
./node_modules/.bin/parcel bundles-src/index.js --dist-dir bundles --public-url="./"
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
deactivate
systemctl reload nginx
systemctl restart starburger
set -o allexport && source .env && set +o allexport
curl https://api.rollbar.com/api/1/deploy/ \
  -F access_token=$ROLLBAR_ACCESS_TOKEN \
  -F environment=$ENVIROMENT  \
  -F revision=$(git rev-parse --verify HEAD) \
  -F local_username='Jaggmort'
