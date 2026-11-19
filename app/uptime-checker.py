import json
import threading
import time
import redis
import requests
from flask import Flask, jsonify, request
import os

REDIS_HOST=os.environ["REDIS_HOST"]
REDIS_PORT=int(os.environ["REDIS_PORT"])

app = Flask(__name__)
db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

CHECK_EVERY_SECONDS = 10
URLS_KEY = "urls"
STATUS_KEY = "statuses"

def check_urls():
    while True:
        urls = db.smembers(URLS_KEY)
        for url in urls:
            start_time = time.time()
            try:
                response = requests.get(url, timeout=5)
                latency = round((time.time() - start_time) * 1000)

                result = {
                    "state": "up" if response.ok else "down",
                    "code": response.status_code,
                    "latency": latency,
                }
            except requests.RequestException:
                result = {
                    "state": "down",
                    "code": None,
                    "latency": None,
                }

            db.hset(STATUS_KEY, url, json.dumps(result))

        time.sleep(CHECK_EVERY_SECONDS)

@app.post("/urls")
def add_url():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Invalid URL"}), 400

    db.sadd(URLS_KEY, url)
    return jsonify({"message": "URL has been added", "url": url}), 201

@app.get("/status")
def get_status():
    raw_data = db.hgetall(STATUS_KEY)
    results = {url: json.loads(info) for url, info in raw_data.items()}
    return jsonify(results)

@app.get("/healthz")
def healthz():
    try:
        db.ping()
        return jsonify({"app": "ok", "redis": "ok"}), 200
    except redis.ConnectionError:
        return jsonify({"app": "ok", "redis": "disconnect"}), 503

@app.get("/")
def home_page():
    return jsonify({
        "message": "Welcome",
        "valid urls": "/healthz and /status",
        }), 200

if __name__ == '__main__':
    worker = threading.Thread(target=check_urls, daemon=True)
    worker.start()

    app.run(host="0.0.0.0", port=5000)