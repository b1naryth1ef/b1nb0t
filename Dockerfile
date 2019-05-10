FROM python:3.7

ENV PYTHONUNBUFFERED 1
ENV ENV docker

RUN mkdir /opt/b1nb0t

ADD requirements.txt /opt/b1nb0t
RUN pip install -r /opt/b1nb0t/requirements.txt

ADD . /opt/b1nb0t/
WORKDIR /opt/b1nb0t
