FROM python:3.10

WORKDIR /home/demozoo

RUN apt-get update && \
    apt-get install -y --no-install-recommends iputils-ping && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

COPY requirements.txt ./
RUN pip install -r requirements.txt && rm requirements.txt

COPY ./.docker/web/local.py ./demozoo/settings/local.py

COPY package*.json ./
RUN npm install --no-save

EXPOSE 8000

ENTRYPOINT ["/home/demozoo/.docker/web/entrypoint"]
