# Monitoring Stack for Match List Change Detector

This directory contains a complete monitoring and alerting stack for the Match List Change Detector application.

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification
- **Node Exporter**: Host metrics collection
- **cAdvisor**: Container metrics collection
- **Loki**: Log aggregation
- **Promtail**: Log collection
- **Blackbox Exporter**: External endpoint monitoring
- **Pushgateway**: Push-based metrics collection
- **NGINX**: Secure external access

## Setup

1. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration:
   ```bash
   nano .env
   ```

3. Generate SSL certificates and authentication files:
   ```bash
   ./generate-certs.sh
   ```

4. Start the monitoring stack:
   ```bash
   docker-compose up -d
   ```

## Accessing the Dashboards

- **Grafana**: http://localhost:3000 (default credentials: admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

For secure external access:
- https://monitoring.example.com (replace with your domain)

## Dashboards

The following dashboards are automatically provisioned:

1. **Match List Change Detector**: Application-specific metrics
2. **System Monitoring**: Host-level metrics (CPU, memory, disk, network)
3. **Container Monitoring**: Container-level metrics

## Alerting

Alerts are configured for:

- Application issues (high error rates, processing failures)
- System resource issues (high CPU, memory, disk usage)
- Container issues (container down, high resource usage)

Alerts are sent to:
- Slack (for all alerts)
- Discord (for critical alerts only)

## Configuration

### Prometheus

Prometheus configuration is in `prometheus/prometheus.yml`. Alert rules are in `prometheus/rules/`.

### Alertmanager

Alertmanager configuration is in `alertmanager/alertmanager.yml`. Notification templates are in `alertmanager/templates/`.

### Grafana

Grafana datasources and dashboards are automatically provisioned from `grafana/provisioning/`.

### Loki

Loki configuration is in `loki/loki-config.yml`.

### Promtail

Promtail configuration is in `promtail/promtail-config.yml`.

### NGINX

NGINX configuration is in `nginx/nginx.conf` and `nginx/conf.d/monitoring.conf`.

## Customization

To add custom dashboards, place JSON files in `grafana/dashboards/`.

To add custom alert rules, add YAML files to `prometheus/rules/`.

To customize notification templates, edit files in `alertmanager/templates/`.
