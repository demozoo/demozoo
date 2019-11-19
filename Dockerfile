FROM ubuntu:trusty

VOLUME ["/home/demozoo"]

WORKDIR /home/demozoo

COPY ./etc/vagrant-provision.sh ./etc/vagrant-provision.sh

RUN chmod +x ./etc/vagrant-provision.sh && ./etc/vagrant-provision.sh

EXPOSE 8000

ENTRYPOINT ["/home/demozoo/manage.py", "runserver", "0.0.0.0:8000"]