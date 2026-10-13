FROM python:3.14-alpine

RUN apk update && apk upgrade \
    && apk add --no-cache gcc musl-dev libffi-dev make

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY gitops_updater /app/gitops_updater
COPY main.py /app/main.py

EXPOSE 80

CMD ["gunicorn", "--bind", "0.0.0.0:80", "gitops_updater.main:app"]
