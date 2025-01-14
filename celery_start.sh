#!/bin/bash

nohup /opt/conda/envs/favicondb/bin/celery -A minitask.get_favicom.celery_app worker --loglevel=info &

/opt/conda/envs/favicondb/bin/python main.py

