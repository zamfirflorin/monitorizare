# app.py
import os

from flask import Flask, request, g, jsonify
from datetime import datetime
import uuid
import time
import json
import logging

# Ensure log directory exists
os.makedirs("/var/log/myapp", exist_ok=True)

# Setup logger
logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("/var/log/myapp/app.log")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')  # store raw JSON
fh.setFormatter(formatter)
logger.addHandler(fh)

app = Flask(__name__)

def uid():
    return uuid.uuid4().hex[:12]

@app.before_request
def start_span():
    g.trace_id = request.headers.get("X-Trace-ID", uid() * 2)      # 32 chars
    g.span_id  = uid()
    g.parent_span_id = request.headers.get("X-Span-ID")
    g.start = time.time()

@app.after_request
def end_span(response):
    duration = int((time.time() - g.start) * 1000)
    log = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "service": "serviciu-login",
        "trace_id": g.trace_id,
        "span_id": g.span_id,
        "parent_span_id": g.parent_span_id or None,
        "duration_ms": duration,
        "path": request.path,
        "status_code": response.status_code,
        "message": "request completed"
    }
    logger.info(json.dumps(log))

    # propagăm mai departe către alte microservicii
    response.headers["X-Trace-ID"] = g.trace_id
    response.headers["X-Span-ID"]  = g.span_id
    return response

@app.route("/login")
def login():
    time.sleep(0.05 + 0.15 * (hash(g.trace_id) % 100)/100)  # simulare latență
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)