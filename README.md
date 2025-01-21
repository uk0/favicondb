## favicondb （获取网站的favicon图标）

 A Simple favicon database

* 默认第一次会返回灰色地球，后续会返回真实的favicon图标（当task运行完成后。）


* examples 

```bash

http://127.0.0.1:8000/api/v1/favicon/https://x.com

or

http://127.0.0.1:8000/api/v1/favicon/x.com

```

![img.png](img.png)


### install python dependencies and dev running.

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

* start web server

```bash

 python main.py
 
```



### quick start (docker)



* docker build

```bash

docker build --platform=linux/amd64  -t firshme/favicondb  -f Dockerfile .

```

* docker-compose start 

```bash

docker-compose up -d

```
