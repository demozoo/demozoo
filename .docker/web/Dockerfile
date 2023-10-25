FROM python:3.10

VOLUME ["/home/demozoo"]

WORKDIR /home/demozoo

RUN apt-get update && \
    apt-get install -y --no-install-recommends iputils-ping && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt && rm requirements.txt

COPY ./.docker/web/local.py ./demozoo/settings/local.py

EXPOSE 8000

ENTRYPOINT ["/home/demozoo/.docker/web/entrypoint"]
