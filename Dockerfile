# build time
FROM python:3.12.7-slim-bookworm@sha256:60d9996b6a8a3689d36db740b49f4327be3be09a21122bd02fb8895abb38b50d AS buildtime
WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# create isolated environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# install libraries
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# runtime
FROM python:3.12.7-slim-bookworm@sha256:60d9996b6a8a3689d36db740b49f4327be3be09a21122bd02fb8895abb38b50d AS runtime
WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    REDIS_HOST=localhost \
    REDIS_PROT=6379

# COPY app
COPY ./app ./

RUN useradd --system --no-create-home --shell /usr/sbin/nologin uptime

COPY --from=buildtime /opt/venv /opt/venv

RUN chown -R root:uptime /app /opt/venv && \
    chmod -R 750 /app /opt/venv

USER uptime

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/', timeout=3)"]

ENTRYPOINT ["python3", "uptime-checker.py"]