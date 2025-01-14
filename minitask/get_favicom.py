import asyncio
import base64
import io
import re
from urllib.parse import urlparse, urljoin

from PIL import Image
import redis
import logging
import cairosvg

from playwright.async_api import async_playwright
from celery import Celery

logging.basicConfig(level=logging.INFO)

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/1",
    backend="redis://redis:6379/2",
)


async def get_favicon_task(url):
    logging.info(f"get_favicon_task is start {url}")
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    key = f"favicon:{host}"
    r = redis.Redis(host='redis', port=6379, db=6)

    job_key = f"job:favicon:{host}"
    r.setex(job_key, 60, 1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--ignore-certificate-errors",
                "--disable-web-security",
                "--window-size=400,300"
            ]
        )
        page = await browser.new_page()
        await page.set_viewport_size({"width": 400, "height": 300})
        await page.goto(url, wait_until="networkidle", timeout=30000)

        favicon = await page.evaluate("""
            () => {
                const getAttr = (el, attr) => el ? el.getAttribute(attr) : null;
                let link = document.querySelector('link[rel="shortcut icon"]')
                    || document.querySelector('link[rel="icon"]');
                if (link) return getAttr(link, 'href');
                let meta = document.querySelector('meta[property="og:image"]');
                if (meta) return getAttr(meta, 'content');
                let metaItem = document.querySelector('meta[itemprop="image"]');
                if (metaItem) return getAttr(metaItem, 'content');
                return null;
            }
        """)

        page_url = page.url


        if favicon:
            if not re.match(r'^https?://|^data:', favicon):
                favicon = urljoin(page_url, favicon, allow_fragments=True)
            logging.info(f"favicon url {favicon}")

            favicon_data = None
            if favicon.startswith("data:image/"):
                base64_part = favicon.split(",", 1)[1]
                favicon_data = base64.b64decode(base64_part)
            else:
                # 用fetch拿二进制再base64
                try:
                    base64_str = await page.evaluate(f"""
                    async () => {{
                        const resp = await fetch("{favicon}");
                        const buf = await resp.arrayBuffer();
                        return btoa(String.fromCharCode(...new Uint8Array(buf)));
                    }}
                    """)
                    favicon_data = base64.b64decode(base64_str)
                except Exception as e:
                    logging.warning(f"获取 favicon 失败: {e}")

            await browser.close()
            r.delete(job_key)
            if favicon_data:
                if b"<svg" in favicon_data[:500].lower():
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
                logging.info("no get favicon icon.")
        else:
            logging.info("页面中未找到 favicon 或图标")


@celery_app.task
def task_fet(url):
    asyncio.run(get_favicon_task(url))