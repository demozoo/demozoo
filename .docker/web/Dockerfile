FROM python:2.7.17

VOLUME ["/home/demozoo"]

WORKDIR /home/demozoo

COPY requirements.txt ./
RUN pip install -r requirements.txt && rm requirements.txt

COPY ./.docker/web/local.py ./demozoo/settings/local.py

EXPOSE 8000

ENTRYPOINT ["/home/demozoo/.docker/web/entrypoint"]
