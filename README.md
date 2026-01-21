# Prometheus Sample Application for PromQL Tricks

A sample application with comprehensive Prometheus metrics designed to demonstrate RED (Rate, Errors, Duration) and USE (Utilization, Saturation, Errors) metrics, as well as advanced PromQL use cases.

## Overview

This sample application provides:
- **RED Metrics**: Rate, Errors, Duration for HTTP requests
- **USE Metrics**: Utilization, Saturation, Errors for system resources
- **Special Metrics**: Timestamp gauges, multi-label metrics, and metrics designed for advanced PromQL queries

## Architecture

- **Sample App**: Flask application running on port 8000
- **Node Exporter**: System metrics exporter (CPU, disk, memory) on port 9100
- **Prometheus**: Metrics collection and storage on port 9090
- **Docker Compose**: Orchestrates all services

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Bash shell (for the exercise script)

### Starting the Environment

1. Start the services:
```bash
docker-compose up -d
```

2. Verify services are running:
```bash
docker-compose ps
```

3. Access the services:
- **Application**: http://localhost:8000
- **Prometheus UI**: http://localhost:9090
- **Application Metrics**: http://localhost:8000/metrics
- **Node Exporter Metrics**: http://localhost:9100/metrics

### Generating Traffic

Run the exercise script to generate various types of traffic:

```bash
chmod +x exercise_app.sh
./exercise_app.sh
```

Or set a custom base URL:
```bash
BASE_URL=http://localhost:8000 ./exercise_app.sh
```

The script will continuously make requests to various endpoints, generating metrics that demonstrate different PromQL use cases.

## Metrics Exported

### RED Metrics (Rate, Errors, Duration)

- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: Request duration histogram
- `http_request_duration_summary_seconds`: Request duration summary
- `http_errors_total`: Total HTTP errors by method, endpoint, and error type

### USE Metrics (Utilization, Saturation, Errors)

- `cpu_utilization_percent`: CPU utilization by server and region
- `memory_utilization_bytes`: Memory utilization by server and region
- `active_connections`: Active connections by server and region
- `queue_depth`: Queue depth by queue name and priority

### Business Metrics

- `orders_total`: Total orders by status and region
- `order_value_total`: Total order value by product category, payment method, region, and status
- `products_viewed_total`: Total products viewed by category and region

### Special Metrics for PromQL Examples

- `last_order_timestamp_seconds`: Timestamp gauge for last order by order type and region
- `last_user_login_timestamp_seconds`: Timestamp gauge for last user login by user tier
- `api_calls_total`: API calls by version and endpoint (for fill missing data examples)

### Node Exporter Metrics (System Metrics)

The node-exporter provides system-level metrics from the host (or Docker VM):

**CPU Metrics:**
- `node_cpu_seconds_total`: CPU time spent in each mode (user, system, idle, etc.)
- `node_load1`, `node_load5`, `node_load15`: System load averages

**Memory Metrics:**
- `node_memory_MemTotal_bytes`: Total memory
- `node_memory_MemAvailable_bytes`: Available memory
- `node_memory_MemFree_bytes`: Free memory
- `node_memory_Buffers_bytes`: Buffered memory
- `node_memory_Cached_bytes`: Cached memory

**Disk Metrics:**
- `node_disk_io_time_seconds_total`: Time spent doing I/O
- `node_disk_read_bytes_total`: Total bytes read
- `node_disk_write_bytes_total`: Total bytes written
- `node_filesystem_size_bytes`: Filesystem size
- `node_filesystem_avail_bytes`: Available filesystem space
- `node_filesystem_free_bytes`: Free filesystem space

**Note**: On macOS, node-exporter collects metrics from the Docker VM, not the macOS host directly.

## PromQL Examples

### 1. Last Time Something Happened (Timestamp Gauge)

Get the last time an order was placed:
```promql
last_order_timestamp_seconds
```

Time since last order:
```promql
time() - last_order_timestamp_seconds
```

### 2. Forecast Using Linear Regression

Forecast request rate:
```promql
predict_linear(rate(http_requests_total[5m])[1h:], 3600)
```

### 3. If/Else (Conditional Logic)

Set error rate to 1 if errors > 100, else 0:
```promql
http_errors_total > 100
```

Or using `clamp_min`/`clamp_max`:
```promql
clamp_min(http_errors_total, 100) / 100
```

### 4. Select Latest Entry of a Timeseries

Latest value of a metric:
```promql
last_over_time(cpu_utilization_percent[1h])
```

### 5. Group Multiple Categories of Labels

Sum order value across all payment methods:
```promql
sum by (product_category, region, status) (order_value_total)
```

Or aggregate across regions:
```promql
sum without (region) (order_value_total)
```

### 6. Fill Missing Data with Zeros

Fill missing API version metrics:
```promql
api_calls_total or on() vector(0)
```

Or for specific labels:
```promql
(
  api_calls_total{api_version="v1"} or on() vector(0)
) + (
  api_calls_total{api_version="v2"} or on() vector(0)
) + (
  api_calls_total{api_version="v3"} or on() vector(0)
)
```

## Example Queries

### Request Rate
```promql
rate(http_requests_total[5m])
```

### Error Rate
```promql
rate(http_errors_total[5m])
```

### 95th Percentile Latency
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### CPU Utilization Average
```promql
avg(cpu_utilization_percent)
```

### Active Connections by Region
```promql
sum by (region) (active_connections)
```

### Order Rate by Region
```promql
rate(orders_total[5m])
```

### Node Exporter Example Queries

**CPU Usage Percentage:**
```promql
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

**Memory Usage Percentage:**
```promql
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

**Disk Usage Percentage:**
```promql
(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100
```

**Disk I/O Rate:**
```promql
rate(node_disk_io_time_seconds_total[5m])
```

**Memory Available:**
```promql
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024  # GB
```

## Stopping the Environment

```bash
docker-compose down
```

To also remove volumes:
```bash
docker-compose down -v
```

## File Structure

```
sample-applications/
├── app.py                 # Flask application with metrics
├── requirements.txt       # Python dependencies
├── Dockerfile            # Application container definition
├── docker-compose.yml    # Docker Compose configuration
├── prometheus.yml        # Prometheus configuration
├── exercise_app.sh       # Script to generate traffic
└── README.md            # This file
```

## Customization

### Changing Scrape Interval

Edit `prometheus.yml`:
```yaml
scrape_interval: 10s  # Change to desired interval
```

### Adding More Endpoints

Add new routes in `app.py` and update `exercise_app.sh` to call them.

### Modifying Metrics

All metrics are defined at the top of `app.py`. You can add new metrics following the same pattern.

## Troubleshooting

### Services won't start
- Check if ports 8000 and 9090 are already in use
- Verify Docker is running: `docker ps`

### No metrics appearing
- Check application logs: `docker-compose logs app`
- Verify Prometheus can reach the app: `curl http://localhost:8000/metrics`
- Check Prometheus targets: http://localhost:9090/targets

### Metrics not updating
- Ensure the exercise script is running
- Check Prometheus scrape configuration
- Verify network connectivity between containers

## Next Steps

1. Explore the Prometheus UI at http://localhost:9090
2. Try the example PromQL queries in the query interface
3. Create Grafana dashboards using these metrics
4. Experiment with alerting rules based on the metrics

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Prometheus Client Library](https://github.com/prometheus/client_python)

