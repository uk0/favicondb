import io

import uvicorn
from fastapi import FastAPI, Response, status
from urllib.parse import urlparse
import redis
import logging
from PIL import Image

from minitask.get_favicom import task_fet

logging.basicConfig(level=logging.INFO)
app = FastAPI()
r = redis.Redis(host='redis', port=6379, db=6)

image = Image.open('default_favicon.png')
new_size = (48, 48)
resized_image = image.resize(new_size)
resized_image.save('resized_default_favicon.png')
from huey import RedisHuey

huey = RedisHuey()

with open("resized_default_favicon.png", "rb") as image_file:
    default_favicon = image_file.read()
@app.get("/api/v1/favicon/{url_path:path}")
def get_favicon(url_path: str):
    # 如果传入的 url_path 是 "csdn.com" 或 "https://xxx" 等
    # 都统一用 urlparse 取 netloc
    # 若没有 scheme，urlparse 得到的 netloc 为空，可以手动补齐
    if not url_path.startswith("http"):
        url_path = "https://" + url_path
    parsed = urlparse(url_path)
    host = parsed.netloc or parsed.path

    key = f"favicon:{host}"
    job_key = f"job:favicon:{host}"
    logging.warning(f"key: {key}")
    data = r.get(key)
    if data:
        return Response(content=data, media_type="image/png")

    job_data = r.get(job_key)
    if job_data:
        return Response(content=default_favicon, status_code=status.HTTP_200_OK, media_type="image/png")
    logging.info(f"task get favicon url_path: {url_path}")
    # start task to get favicon
    task = task_fet.apply_async(args=[url_path, ])
    logging.info(f"task id: {task.id}")
    return Response(content=default_favicon, status_code=status.HTTP_200_OK, media_type="image/png")
if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)