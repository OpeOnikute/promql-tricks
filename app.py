#!/usr/bin/env python3
"""
Sample application for Prometheus metrics demonstration.
Exports RED (Rate, Errors, Duration) and USE (Utilization, Saturation, Errors) metrics.
"""

import time
import random
import threading
from flask import Flask, jsonify, request
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST,
    REGISTRY
)
from prometheus_client.core import CollectorRegistry
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RED Metrics (Rate, Errors, Duration)
# Request counters by endpoint and status
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Request duration summary (alternative to histogram)
http_request_duration_summary = Summary(
    'http_request_duration_summary_seconds',
    'HTTP request duration summary',
    ['method', 'endpoint']
)

# Error counter
http_errors_total = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)

# USE Metrics (Utilization, Saturation, Errors)
# CPU utilization simulation
cpu_utilization_percent = Gauge(
    'cpu_utilization_percent',
    'CPU utilization percentage',
    ['server', 'region']
)

# Memory utilization
memory_utilization_bytes = Gauge(
    'memory_utilization_bytes',
    'Memory utilization in bytes',
    ['server', 'region']
)

# Active connections (saturation metric)
active_connections = Gauge(
    'active_connections',
    'Number of active connections',
    ['server', 'region']
)

# Queue depth (saturation)
queue_depth = Gauge(
    'queue_depth',
    'Queue depth',
    ['queue_name', 'priority']
)

# Special metrics for PromQL examples
# Timestamp gauge - last time something happened
last_order_timestamp = Gauge(
    'last_order_timestamp_seconds',
    'Unix timestamp of the last order',
    ['order_type', 'region']
)

last_user_login_timestamp = Gauge(
    'last_user_login_timestamp_seconds',
    'Unix timestamp of the last user login',
    ['user_tier']
)

# Metrics with multiple label categories for grouping examples
order_value = Counter(
    'order_value_total',
    'Total order value',
    ['product_category', 'payment_method', 'region', 'status']
)

# Metrics that can have missing data (for fill examples)
api_calls_total = Counter(
    'api_calls_total',
    'Total API calls',
    ['api_version', 'endpoint']
)

# Business metrics
orders_total = Counter(
    'orders_total',
    'Total number of orders',
    ['status', 'region']
)

products_viewed_total = Counter(
    'products_viewed_total',
    'Total products viewed',
    ['category', 'region']
)

# Simulate background resource metrics
def update_resource_metrics():
    """Background thread to simulate resource metrics"""
    servers = ['web-1', 'web-2', 'api-1']
    regions = ['us-east', 'us-west', 'eu-central']
    
    while True:
        for server in servers:
            for region in regions:
                # CPU utilization (0-100%)
                cpu_utilization_percent.labels(
                    server=server, region=region
                ).set(random.uniform(20, 95))
                
                # Memory utilization (100MB - 8GB)
                memory_utilization_bytes.labels(
                    server=server, region=region
                ).set(random.uniform(100_000_000, 8_000_000_000))
                
                # Active connections (0-1000)
                active_connections.labels(
                    server=server, region=region
                ).set(random.randint(0, 1000))
        
        # Queue depth
        queues = ['order-queue', 'notification-queue', 'payment-queue']
        priorities = ['high', 'medium', 'low']
        for queue in queues:
            for priority in priorities:
                queue_depth.labels(
                    queue_name=queue, priority=priority
                ).set(random.randint(0, 500))
        
        time.sleep(5)  # Update every 5 seconds

# Start background thread
resource_thread = threading.Thread(target=update_resource_metrics, daemon=True)
resource_thread.start()


@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'sample-app'})


@app.route('/products')
def get_products():
    """Get products - simulates variable latency"""
    start_time = time.time()
    
    # Simulate processing time
    delay = random.uniform(0.01, 0.5)
    time.sleep(delay)
    
    category = random.choice(['electronics', 'clothing', 'books', 'food'])
    region = request.headers.get('X-Region', 'unknown')
    
    products_viewed_total.labels(category=category, region=region).inc()
    
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='GET', endpoint='/products').observe(duration)
    http_request_duration_summary.labels(method='GET', endpoint='/products').observe(duration)
    http_requests_total.labels(method='GET', endpoint='/products', status='200').inc()
    
    return jsonify({
        'products': [
            {'id': 1, 'name': 'Product 1', 'category': category},
            {'id': 2, 'name': 'Product 2', 'category': category}
        ]
    })


@app.route('/orders', methods=['POST'])
def create_order():
    """Create order - simulates order processing"""
    start_time = time.time()
    
    # Simulate processing time
    delay = random.uniform(0.05, 1.0)
    time.sleep(delay)
    
    # Randomly fail some orders (5% error rate)
    if random.random() < 0.05:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(method='POST', endpoint='/orders').observe(duration)
        http_errors_total.labels(method='POST', endpoint='/orders', error_type='validation_error').inc()
        http_requests_total.labels(method='POST', endpoint='/orders', status='400').inc()
        return jsonify({'error': 'Validation failed'}), 400
    
    # Simulate order data
    order_type = random.choice(['standard', 'express', 'premium'])
    region = request.headers.get('X-Region', 'unknown')
    product_category = random.choice(['electronics', 'clothing', 'books'])
    payment_method = random.choice(['credit_card', 'paypal', 'bank_transfer'])
    status = random.choice(['pending', 'processing', 'completed'])
    
    # Update timestamp gauge
    last_order_timestamp.labels(order_type=order_type, region=region).set(time.time())
    
    # Update counters
    orders_total.labels(status=status, region=region).inc()
    order_value.labels(
        product_category=product_category,
        payment_method=payment_method,
        region=region,
        status=status
    ).inc(random.uniform(10, 1000))
    
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='POST', endpoint='/orders').observe(duration)
    http_request_duration_summary.labels(method='POST', endpoint='/orders').observe(duration)
    http_requests_total.labels(method='POST', endpoint='/orders', status='201').inc()
    
    return jsonify({
        'order_id': random.randint(1000, 9999),
        'status': status,
        'type': order_type
    }), 201


@app.route('/users/<int:user_id>/login', methods=['POST'])
def user_login(user_id):
    """User login - updates timestamp gauge"""
    start_time = time.time()
    
    delay = random.uniform(0.02, 0.3)
    time.sleep(delay)
    
    user_tier = random.choice(['free', 'premium', 'enterprise'])
    
    # Update timestamp gauge for last login
    last_user_login_timestamp.labels(user_tier=user_tier).set(time.time())
    
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='POST', endpoint='/users/login').observe(duration)
    http_requests_total.labels(method='POST', endpoint='/users/login', status='200').inc()
    
    return jsonify({'user_id': user_id, 'tier': user_tier, 'logged_in': True})


@app.route('/api/v1/data')
def api_v1_data():
    """API v1 endpoint - for fill missing data examples"""
    api_calls_total.labels(api_version='v1', endpoint='/data').inc()
    return jsonify({'data': 'v1 response'})


@app.route('/api/v2/data')
def api_v2_data():
    """API v2 endpoint - for fill missing data examples"""
    api_calls_total.labels(api_version='v2', endpoint='/data').inc()
    return jsonify({'data': 'v2 response'})


@app.route('/api/v3/data')
def api_v3_data():
    """API v3 endpoint - may not be called (for fill examples)"""
    api_calls_total.labels(api_version='v3', endpoint='/data').inc()
    return jsonify({'data': 'v3 response'})


@app.route('/slow')
def slow_endpoint():
    """Slow endpoint - for duration analysis"""
    start_time = time.time()
    
    # Simulate slow processing
    delay = random.uniform(1.0, 3.0)
    time.sleep(delay)
    
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='GET', endpoint='/slow').observe(duration)
    http_requests_total.labels(method='GET', endpoint='/slow', status='200').inc()
    
    return jsonify({'message': 'Slow response completed'})


@app.route('/error')
def error_endpoint():
    """Error endpoint - for error rate analysis"""
    start_time = time.time()
    
    error_type = random.choice(['timeout', 'database_error', 'validation_error'])
    http_errors_total.labels(method='GET', endpoint='/error', error_type=error_type).inc()
    
    duration = time.time() - start_time
    http_request_duration_seconds.labels(method='GET', endpoint='/error').observe(duration)
    http_requests_total.labels(method='GET', endpoint='/error', status='500').inc()
    
    return jsonify({'error': error_type}), 500


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(REGISTRY), 200, {'Content-Type': CONTENT_TYPE_LATEST}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)

