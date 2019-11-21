FROM ubuntu:trusty

VOLUME ["/home/demozoo"]

WORKDIR /home/demozoo

ENV PROJECT_DIR=/home/demozoo,
ENV VIRTUALENV_DIR=/home/.virtualenvs/demozoo
ENV PIP=$VIRTUALENV_DIR/bin/pip
ENV PYTHON=$VIRTUALENV_DIR/bin/python

RUN apt-get update -y && \
    # Python 2.7
    apt-get install -y python python-dev python-pip && \
    # PostgreSQL
    apt-get install -y postgresql libpq-dev && \
    # libffi
    # (needed by bcrypt, which some old accounts still use as their password encryption method)
    apt-get install -y libffi-dev && \
    # xapian (search engine)
    apt-get install -y python-xapian

# node.js
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get install -y nodejs

# virtualenvwrapper
RUN pip install virtualenvwrapper
RUN echo 'export WORKON_HOME=\$HOME/.virtualenvs; \n\
source /usr/local/bin/virtualenvwrapper.sh; \n\
workon demozoo;' >> /home/demozoo/.bashrc

# Create virtualenv
RUN /usr/local/bin/virtualenv $VIRTUALENV_DIR && \
    echo $PROJECT_DIR > $VIRTUALENV_DIR/.project && \
    $PIP install -r $PROJECT_DIR/requirements.txt

# link xapian into virtualenv
RUN ln -s /usr/lib/python2.7/dist-packages/xapian $VIRTUALENV_DIR/lib/python2.7/site-packages/

EXPOSE 8000

ENTRYPOINT ["/home/demozoo/manage.py", "runserver", "0.0.0.0:8000"]