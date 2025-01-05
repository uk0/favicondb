## favicondb

 A Simple favicon database

### install python dependencies

```bash
 conda create --name favicondb --file conda.env
```


### base dependencies

```bash
docker run -itd --name redis-server -p 6379:6379 redis
```



### fix 

>OSError: no library called "cairo-2" was found (from Custom_Widgets import ProjectMaker)

```bash
conda install cairo pango
```