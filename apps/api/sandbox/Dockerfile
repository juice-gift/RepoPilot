FROM public.ecr.aws/docker/library/python@sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f
COPY requirements.txt /opt/repopilot/requirements.txt
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r /opt/repopilot/requirements.txt
COPY run_tests.py /opt/repopilot/run_tests.py
ENV PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
USER 65534:65534
WORKDIR /tmp
ENTRYPOINT ["python", "-I", "-B", "/opt/repopilot/run_tests.py"]
