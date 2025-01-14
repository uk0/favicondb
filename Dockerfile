FROM continuumio/miniconda3

SHELL ["/bin/bash", "-c"]

ADD . /home/dev/
WORKDIR /home/dev/

RUN apt-get update && apt-get install -y \
    libasound2 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxcursor1 \
    libxi6 \
    libxss1 \
    libxext6 \
    libxshmfence-dev \
    libgtk-3-0 \
    libgbm-dev \
    libpangocairo-1.0-0 \
    gconf-service \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN conda create -n favicondb python=3.10 -y && \
    conda run -n favicondb conda install cairo pango -y && \
    conda run -n favicondb python -m pip install -r requirements.txt && \
    conda run -n favicondb playwright install
CMD ["./celery_start.sh"]