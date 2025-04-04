#!/bin/bash

# Generate self-signed SSL certificate for NGINX
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/server.key \
  -out nginx/certs/server.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=monitoring.example.com"

# Generate htpasswd files for basic authentication
# Default credentials: admin/admin
htpasswd -bc nginx/auth/prometheus.htpasswd admin admin
htpasswd -bc nginx/auth/alertmanager.htpasswd admin admin

echo "Certificates and authentication files generated successfully."
