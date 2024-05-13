FROM ubuntu:22.04

RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3.10 python3-pip curl vim supervisor

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    update-alternatives --set python3 /usr/bin/python3.10 && \
    curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/redis.list
RUN apt-get update && apt-get install -y redis && \
    service redis-server start && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

EXPOSE 8001

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
