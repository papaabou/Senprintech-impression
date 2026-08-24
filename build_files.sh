#!/usr/bin/env bash
set -o errexit

python3.12 -m pip install --upgrade pip
pip3.12 install -r requirements.txt
python3.12 manage.py collectstatic --no-input
python3.12 manage.py migrate --no-input
python3.12 manage.py create_initial_superuser
python3.12 manage.py seed_senprintech
