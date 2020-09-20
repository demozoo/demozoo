FROM python:2.7.17

ENV DJANGO_SETTINGS_MODULE="demozoo.settings.dev"
ENV PROJECT_DIR="/home"

VOLUME ["/home/demozoo"]

WORKDIR /home/demozoo

COPY requirements.txt ./
RUN pip install -r requirements.txt && rm requirements.txt

COPY ./.docker/create-local.py.sh ./
RUN ./create-local.py.sh && rm ./create-local.py.sh

EXPOSE 8000

ENTRYPOINT ["/home/demozoo/manage.py", "runserver", "0.0.0.0:8000"]
