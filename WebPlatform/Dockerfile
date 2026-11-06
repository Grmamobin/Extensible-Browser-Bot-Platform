FROM selenium/standalone-chrome:latest

USER root
ENV DISPLAY=:99

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

CMD Xvfb :99 -screen 0 1920x1080x24 & \
    x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -rfbport 5900 & \
    python3 app.py