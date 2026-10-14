# syntax=docker/dockerfile:1

# Named stage so Dependabot updates this image. CI installs the same tag.
FROM ghcr.io/astral-sh/uv:0.13.0@sha256:cdc6093146eb3ff6a40107b38f008b789e050e77ad87865e381d9917da55a168 AS uv

FROM python:3.14-alpine AS builder

RUN apk update && apk upgrade \
    && apk add --no-cache gcc musl-dev libffi-dev make \
    && rm -rf /var/cache/apk/*

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.14-alpine AS runtime

RUN apk update && apk upgrade \
    && apk add --no-cache libffi \
    && rm -rf /var/cache/apk/*

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv
COPY gitops_updater /app/gitops_updater
COPY main.py /app/main.py
COPY gunicorn_conf.py /app/gunicorn_conf.py

RUN adduser -u 1001 -D gitops-updater \
    && chown -R gitops-updater:gitops-updater /app

USER gitops-updater

EXPOSE 8080

CMD ["gunicorn", "--conf", "/app/gunicorn_conf.py", "--bind", "0.0.0.0:8080", "gitops_updater.main:app", "--logger-class", "gitops_updater.logger.CustomGunicornLogger"]
