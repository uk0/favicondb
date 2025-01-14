## favicondb

 A Simple favicon database

### install python dependencies

```bash

 conda create -n "favicondb" python==3.10
 
```

```bash

 conda activate favicondb
 
```

```bash

 pip install -r requirements.txt
 
```


### start server

* start celery worker


```bash

 celery -A minitask.get_favicom.celery_app worker --loglevel=info
 
```

* start server


```bash

 python main.py
 
```

### quick start

* docker build

```bash

docker build --platform=linux/amd64  -t firshme/favicondb  -f Dockerfile .

```

* docker-compose start 

```bash

docker-compose up -d

```
