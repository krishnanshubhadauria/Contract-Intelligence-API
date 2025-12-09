from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Metrics
ingest_counter = Counter('contract_ingest_total', 'Total number of documents ingested')
extract_counter = Counter('contract_extract_total', 'Total number of extraction requests')
ask_counter = Counter('contract_ask_total', 'Total number of Q&A requests')
audit_counter = Counter('contract_audit_total', 'Total number of audit requests')
request_duration = Histogram('contract_request_duration_seconds', 'Request duration in seconds')

def setup_metrics():
    """Initialize metrics"""
    pass

def get_metrics():
    """Get metrics in Prometheus format"""
    return generate_latest()

