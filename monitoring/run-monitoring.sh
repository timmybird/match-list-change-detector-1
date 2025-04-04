#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit the .env file with your configuration."
fi

# Check if certificates exist
if [ ! -f nginx/certs/server.crt ]; then
    echo "Generating certificates and authentication files..."
    ./generate-certs.sh
fi

# Start the monitoring stack
echo "Starting monitoring stack..."
docker-compose up -d

echo "Monitoring stack started!"
echo "Grafana: http://localhost:3000 (default credentials: admin/admin)"
echo "Prometheus: http://localhost:9090"
echo "Alertmanager: http://localhost:9093"
echo "Secure access: https://localhost:8443"
