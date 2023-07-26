#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/starburger/
git pull git@github.com:Jaggmort/star-burger.git master
python3 -m venv .venv
sudo apt update
sudo apt install nodejs
sudo apt install npm
sudo /bin/dd if=/dev/zero of=/var/swap.1 bs=1M count=1024
sudo /sbin/mkswap /var/swap.1
sudo /sbin/swapon /var/swap.1
npm ci --dev
./node_modules/.bin/parcel bundles-src/index.js --dist-dir bundles --public-url="./"
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
echo yes | python manage.py collectstatic
deactivate
systemctl reload nginx
systemctl restart starburger
source .venv/bin/activate
python -c "from environs import Env; env = Env(); env.read_env(); import subprocess; subprocess.run(['/opt/starburger/rollbar', ''], shell=True)"
deactivate
