FROM golang:alpine3.6 AS whoami
ADD . /app
WORKDIR /app
RUN go build -o http


FROM envoyproxy/envoy-alpine:3b75abab717f2c824d3b32b1afcf3383a8cb65ff

ENV PORT 8080

COPY --from=whoami /app/http /usr/app/http

RUN apk add --no-cache --update curl python3 tini && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache
RUN pip install requests uuid click

COPY ./autopilot.py /autopilot.py
COPY ./watch.py /watch.py
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./envoy-bootstrap.yaml /usr/app/envoy-bootstrap.yaml

WORKDIR /usr/app

EXPOSE 8000 8080
ENTRYPOINT ["/sbin/tini", "-vv", "-g", "--", "/entrypoint.sh"]
