FROM golang:1.24-alpine AS builder
WORKDIR /app

COPY go.mod ./
COPY cmd cmd
COPY internal internal

RUN go build -o /edge ./cmd/edge

FROM alpine:3.21
WORKDIR /app

COPY --from=builder /edge /usr/local/bin/edge

EXPOSE 8082
CMD ["edge"]
