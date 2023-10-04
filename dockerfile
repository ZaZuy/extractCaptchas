FROM ubuntu:latest

RUN apt-get update

RUN apt-get install -y python3-pip

RUN mkdir /extractCaptchas
WORKDIR /extractCaptchas
COPY requirements.txt /extractCaptchas/requirements.txt

RUN pip3 install -r requirements.txt
