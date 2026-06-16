# ARL Dockerfile - Ubuntu 24.04 LTS + Python 3.12
#
# === 构建前准备 ===
# 可选 1: ARL-NPoC (PoC 插件引擎)
#   git clone --depth 1 https://github.com/Aabyss-Team/ARL-NPoC docker/ARL-NPoC
#   跳过则 PoC 扫描功能不可用
#
# 可选 2: GeoLite2 (IP 地理定位)
#   从 MaxMind 下载 GeoLite2-City.mmdb + GeoLite2-ASN.mmdb 放入 docker/GeoLite2/
#   https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
#   跳过则 IP 定位信息为空
#
# 构建: docker build -t arl:latest -f docker/Dockerfile .

# -- 构建阶段: 编译 massdns + ncrack --
FROM ubuntu:24.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git make gcc libssl-dev zlib1g-dev ca-certificates wget tar \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/blechschmidt/massdns.git /opt/massdns \
    && cd /opt/massdns && make && cp bin/massdns /usr/local/bin/

RUN wget -q https://nmap.org/ncrack/dist/ncrack-0.7.tar.gz -O /tmp/ncrack.tar.gz \
    && tar -xzf /tmp/ncrack.tar.gz -C /tmp && cd /tmp/ncrack-0.7 \
    && ./configure --quiet && make -j$(nproc) \
    && cp ncrack /usr/local/bin/ && mkdir -p /usr/local/share/ncrack \
    && cp ncrack-services /usr/local/share/ncrack/

# -- 运行阶段 --
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV TZ=Asia/Shanghai

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    nginx curl wget unzip ca-certificates nmap \
    fontconfig fonts-wqy-microhei \
    && ln -s /usr/bin/python3 /usr/bin/python3.6 \
    && rm -rf /var/lib/apt/lists/*

# 编译产物
COPY --from=builder /usr/local/bin/massdns app/tools/massdns
COPY --from=builder /usr/local/bin/ncrack /usr/local/bin/ncrack
COPY --from=builder /usr/local/share/ncrack/ncrack-services /usr/local/share/ncrack/ncrack-services

# 应用代码 + 前端 + 配置
COPY app/ app/
COPY requirements.txt .
COPY docker/frontend/ frontend/
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/worker/gen_crt.sh /usr/bin/gen_crt.sh
COPY docker/worker/wait-for-it.sh /usr/bin/wait-for-it.sh
RUN chmod +x /usr/bin/gen_crt.sh /usr/bin/wait-for-it.sh

# PhantomJS
COPY app/tools/phantomjs /usr/bin/phantomjs
RUN chmod +x /usr/bin/phantomjs

# GeoLite2 (空目录 = 跳过, 有文件 = 启用)
COPY docker/GeoLite2/ /data/GeoLite2/
RUN if [ ! -f /data/GeoLite2/GeoLite2-City.mmdb ]; then \
    echo "NOTE: GeoLite2 not provided, IP geo info will be empty"; fi

# ARL-NPoC (空目录 = 跳过, 有文件 = 启用)
COPY docker/ARL-NPoC/ /opt/ARL-NPoC/
RUN if [ -f /opt/ARL-NPoC/setup.py ] || [ -f /opt/ARL-NPoC/pyproject.toml ]; then \
    echo "Installing ARL-NPoC..."; \
    else echo "NOTE: ARL-NPoC not provided, PoC features disabled"; fi

# Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# ARL-NPoC 安装
RUN if [ -f /opt/ARL-NPoC/setup.py ] || [ -f /opt/ARL-NPoC/pyproject.toml ]; then \
    pip3 install --no-cache-dir -e /opt/ARL-NPoC/ --break-system-packages; \
    if [ -f /opt/ARL-NPoC/requirements.txt ]; then \
    pip3 install --no-cache-dir -r /opt/ARL-NPoC/requirements.txt --break-system-packages; fi; fi

# nuclei
ARG NUCLEI_VERSION=3.2.4
RUN wget -q "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip" \
    && unzip -q "nuclei_${NUCLEI_VERSION}_linux_amd64.zip" nuclei \
    && mv nuclei /usr/bin/ && rm "nuclei_${NUCLEI_VERSION}_linux_amd64.zip" && nuclei -ut

# WebInfoHunter
RUN wget -q https://github.com/Aabyss-Team/arl_files/raw/master/wih/wih_linux_amd64 -O /usr/bin/wih \
    && chmod +x /usr/bin/wih

# SSL DH 参数
RUN curl -sSL https://ssl-config.mozilla.org/ffdhe2048.txt -o /etc/ssl/certs/dhparam.pem

# Nginx 用户
RUN useradd -s /bin/false nginx 2>/dev/null; exit 0

# 自检
RUN cp app/config.yaml.example app/config.yaml \
    && python3 -m flask --app app.main:arl_app routes

EXPOSE 443 5003

CMD ["sh", "-c", "gen_crt.sh && nginx && wait-for-it.sh mongodb:27017 && wait-for-it.sh rabbitmq:5672 && wait-for-it.sh redis:6379 && exec gunicorn -b 0.0.0.0:5003 app.main:arl_app -w 3 --access-logfile /dev/stdout"]
