#!/bin/bash
cd /var/www/www-root/data/www/systemetech.ru
source venv/bin/activate
python main.py "$@"
