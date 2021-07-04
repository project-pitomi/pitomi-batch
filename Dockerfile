FROM python:3-alpine

RUN apk add --update --no-cache sed musl-dev python3-dev libffi-dev openssl-dev cargo rust gcc libavif-dev imagemagick imagemagick-dev
RUN sed -i 's|<!-- <policy domain="resource" name="height" value="10KP"/> -->|<policy domain="resource" name="height" value="20KP"/>|g' /etc/ImageMagick-7/policy.xml
RUN sed -i 's|<!-- <policy domain="resource" name="width" value="10KP"/> -->|<policy domain="resource" name="width" value="20KP"/>|g' /etc/ImageMagick-7/policy.xml

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir resource

COPY src src
