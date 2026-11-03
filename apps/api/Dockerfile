FROM public.ecr.aws/docker/library/python@sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f AS build
RUN pip install --no-cache-dir uv==0.11.8
WORKDIR /app/apps/api
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --no-editable

FROM public.ecr.aws/docker/library/python@sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f
ENV PATH="/app/apps/api/.venv/bin:$PATH" PYTHONPATH=/app/apps/api/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/apps/api
COPY --from=build /app/apps/api/.venv ./.venv
COPY apps/api/src ./src
COPY apps/api/migrations ./migrations
COPY apps/api/alembic.ini ./
COPY apps/api/evaluation ./evaluation
RUN mkdir -p /run/repopilot-api && chown 65534:65534 /run/repopilot-api && chmod 700 /run/repopilot-api
USER 65534:65534
EXPOSE 8000
CMD ["uvicorn", "repopilot.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--limit-concurrency", "32", "--timeout-keep-alive", "5"]
