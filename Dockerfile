FROM python:3.7-alpine3.17
LABEL maintainer="qule520@126.com"

WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD http-forwarder.py .

ENTRYPOINT [ "python", "http-forwarder.py" ]
