#!/usr/bin/env bash
set -o errexit

gunicorn ecommercesite.wsgi:application
