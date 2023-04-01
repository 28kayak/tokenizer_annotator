# base image
# a little overkill but need it to install dot cli for dtreeviz
#FROM ubuntu:18.04

# ubuntu installing - python, pip, graphviz, nano, libpq (for psycopg2)
#RUN apt-get update &&\
#    apt-get install python3.8 -y &&\
#    apt-get install python3-pip -y &&\
#    apt-get install graphviz -y &&\
#    apt-get install nano -y &&\
#    apt-get install libpq-dev -y

# exposing default port for streamlit
#EXPOSE 8501

# making directory of app
#WORKDIR /streamlit-docker

# copy over requirements
#COPY requirements.txt ./requirements.txt

# installing required packages
#RUN pip3 install -r requirements.txt

# copying all app files to image
#COPY . .

# cmd to launch app when container is run
#RUN /db_credentials.sh


#CMD streamlit run app.py

FROM python:3.7

WORKDIR /usr/src/app

# dont write pyc files
# dont buffer to stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /usr/src/app/requirements.txt

# dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && rm -rf /root/.cache/pip

COPY ./ /usr/src/app

CMD python3 scripts/load_docker_db.py