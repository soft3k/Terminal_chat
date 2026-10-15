FROM ubuntu:26.04

LABEL description = "Terminal chat server(C + OpenSSL)"
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev && \
    rm -rf /var/lib/apt/lists/*

COPY server.c .
RUN gcc server.c -o server -lssl -lcrypto

EXPOSE 5050

CMD ["./server"]
