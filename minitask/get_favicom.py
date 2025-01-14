import asyncio
import base64
import io
import re
from urllib.parse import urlparse, urljoin

from PIL import Image
from pyppeteer import launch
import redis
import logging
import cairosvg

logging.basicConfig(level=logging.INFO)


from celery import Celery, shared_task

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/1",
    backend="redis://redis:6379/2",
)


async def get_favicon_task(url):
    # 获取主机名
    logging.info(f"get_favicon_task is start {url}")
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    key = f"favicon:{host}"

    browser = await launch(headless=True, args=[
                                                "--window-size=400,300"
                                                "--no-sandbox",
                                                "--disable-setuid-sandbox",
                                                "--disable-dev-shm-usage",
                                                "--disable-gpu"
                                                ])
    page = await browser.newPage()
    await page.setViewport({"width": 400, "height": 300})
    # 一次 goto 即可
    await page.goto(url, {"waitUntil": "networkidle2", "timeout": 30000})

    # 尝试多种方式获取 favicon
    favicon = await page.evaluate("""
        () => {
            const getAttr = (el, attr) => el ? el.getAttribute(attr) : null;
            // 先尝试 <link rel="shortcut icon"> / <link rel="icon">
            let link = document.querySelector('link[rel="shortcut icon"]')
                || document.querySelector('link[rel="icon"]');
            if (link) return getAttr(link, 'href');
            // 再尝试 og:image
            let meta = document.querySelector('meta[property="og:image"]');
            if (meta) return getAttr(meta, 'content');
            // 尝试
             let metaItem = document.querySelector('meta[itemprop="image"]');
             if (metaItem) return getAttr(metaItem, 'content');
            return null;
        }
    """)

    url = page.url
    if favicon:
        # 若是相对路径，补全为绝对路径
        if not re.match(r'^https?://|^data:', favicon):
            favicon = urljoin(url, favicon,allow_fragments=True)

        logging.info(f"favicon url {favicon}")

        r = redis.Redis(host='redis', port=6379, db=6)
        favicon_data = None

        # 若为 data URI，直接解析
        if favicon.startswith("data:image/"):
            base64_part = favicon.split(",", 1)[1]
            favicon_data = base64.b64decode(base64_part)
        else:
            # 用 JS fetch 获取二进制后再 base64
            fetch_script = f"""
            async () => {{
                const resp = await fetch("{favicon}");
                const buf = await resp.arrayBuffer();
                return btoa(String.fromCharCode(...new Uint8Array(buf)));
            }}
            """
            try:
                base64_str = await page.evaluate(fetch_script)
                favicon_data = base64.b64decode(base64_str)
            except Exception as e:
                logging.warning(f"获取 favicon 失败: {e}")

        await browser.close()

        if favicon_data:
            # 判断是否是 SVG
            if b"<svg" in favicon_data[:500].lower():
                # svg
                try:
                    png_data = cairosvg.svg2png(bytestring=favicon_data)
                    r.set(key, png_data)
                    logging.info(f"SVG 图标已转为 PNG 存入 Redis => {key}")
                except Exception as e:
                    logging.warning(f"SVG 转换 PNG 失败: {e}")
            else:
                try:
                    img = Image.open(io.BytesIO(favicon_data))
                    out = io.BytesIO()
                    img.save(out, format="PNG")
                    r.set(key, out.getvalue())
                    logging.info(f"非 SVG 图标已转为 PNG 存入 Redis => {key}")
                except Exception as e:
                    logging.warning(f"通用格式转 PNG 失败: {e}")
        else:
            logging.info("no get  favicon icon.")
    else:
        logging.info("页面中未找到 favicon 或图标")



@celery_app.task
def task_fet(url):
    asyncio.run(get_favicon_task(url))
