#!/bin/bash

celery -A minitask.get_favicom.celery_app worker --loglevel=info
