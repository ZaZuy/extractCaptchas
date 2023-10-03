FROM ubuntu:16.04

RUN apt-get update
RUN docker run -it -v D:\Python\extractCaptchas:/extractCaptchas -p 8601:8601 --entrypoint /bin/bash tensorflow/serving
RUN docker tensorflow_model_server --rest_api_port=8601  --allow_version_labels_for_unavailable_models --model_config_file=/extractCaptchas/config_model

RUN mkdir /extractCaptchas
WORKDIR /extractCaptchas
COPY requirements.txt /Python/extractCaptchas/requirements.txt
RUN pip install -r requirements.txt
