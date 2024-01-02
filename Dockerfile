FROM python:3.12.1-alpine3.18
LABEL maintainer="qule520@126.com"

WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD http-forwarder.py .

ENTRYPOINT [ "python", "http-forwarder.py" ]
