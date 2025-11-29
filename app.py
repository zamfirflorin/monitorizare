import json
import logging

import time
import uuid

import logstash
from flask import Flask, request, g
# --- OpenTelemetry imports ---
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
# Metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
# Tracing
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import start_http_server, Counter, Gauge, Histogram



# --- App setup ---
app = Flask(__name__)
logging.basicConfig(filename="/tmp/app.log", level=logging.INFO)

# --- Resources ---
resource = Resource(attributes={"service.name": "serviciu-login"})

# --- Tracing setup ---
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",  # adjust if Jaeger runs elsewhere
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
tracer_provider.add_span_processor(span_processor)

tracer = trace.get_tracer(__name__)

# --- Metrics setup ---
metric_reader = PrometheusMetricReader()
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

login_counter = meter.create_counter(
    "login_total", description="Numărul total de încercări de login"
)
login_histogram = meter.create_histogram(
    "login_duration_ms", description="Latența login (ms)"
)

# Start Prometheus metrics endpoint
start_http_server(8000)

logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)
logger.addHandler(logstash.TCPLogstashHandler('localhost', 5044, version=1))

logger.info('Mesaj test trimis către Logstash')

requests_total = Counter('myapp_requests_total', 'Număr total request-uri', ['method', 'endpoint', 'status'])
errors_total = Counter('myapp_errors_total', 'Erori procesate', ['type'])

# Gauge (poate crește/scade)
active_users = Gauge('myapp_active_users', 'Utilizatori activi')

# Histogram (pentru latențe)
request_duration = Histogram('myapp_request_duration_seconds', 'Durata request-urilor', ['endpoint'])

# Pornește serverul de metrici (de obicei pe un port separat)
start_http_server(8000)

# În codul tău:
requests_total.labels(method='GET', endpoint='/api/v1', status='200').inc()
request_duration.labels(endpoint='/api/v1').observe(0.245)
active_users.set(142)
errors_total.labels(type='db_timeout').inc()


# --- Flask route ---
@app.route("/login")
def login():
    time.sleep(0.05 + 0.15 * (hash(g.trace_id) % 100)/100)  # simulare latență
    return "OK", 200

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
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
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
    print(json.dumps(log))   # STDOUT → Filebeat/Logstash

    # propagăm mai departe către alte microservicii
    response.headers["X-Trace-ID"] = g.trace_id
    response.headers["X-Span-ID"]  = g.span_id
    return response



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
