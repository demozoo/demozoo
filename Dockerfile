FROM python:2.7.17

COPY requirements.txt ./
RUN pip install -r requirements.txt

VOLUME ["/home/demozoo"]

WORKDIR /home/demozoo

EXPOSE 8000

ENTRYPOINT ["/home/demozoo/manage.py", "runserver", "0.0.0.0:8000"]
