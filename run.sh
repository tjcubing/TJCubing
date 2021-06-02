#!/bin/bash

# activate venv (pip installed packages)
source venv/bin/activate
# start service with globally installed packages
gunicorn app:app -b $HOST:$PORT --worker-class gevent -w 4 --timeout 600 &>> /site/logs/log.txt

