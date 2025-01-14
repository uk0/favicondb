#!/bin/bash

nohup /opt/conda/envs/favicondb/bin/celery -A minitask.get_favicom.celery_app worker --loglevel=info > sys.log 2>&1 &

nohup /opt/conda/envs/favicondb/bin/python main.py  > sys.log 2>&1 &

tail -f sys.log

