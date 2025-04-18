#!/usr/bin/env python3
"""
Simple health check server for the match list change detector.

Provides a basic HTTP/HTTPS server that responds to health check requests.
"""

import logging
import ssl
import threading
from pathlib import Path
from typing import Optional
from wsgiref.simple_server import make_server

# Get logger
logger = logging.getLogger("health_server")


# Security headers for all responses
SECURITY_HEADERS = [
    ("Content-Type", "application/json"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("X-XSS-Protection", "1; mode=block"),
    ("Content-Security-Policy", "default-src 'none'"),
    ("Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
    ("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"),
    ("Pragma", "no-cache"),
]


# Health check endpoint handler
def health_check_handler(environ, start_response):
    """
    Handle health check requests.

    Args:
        environ: WSGI environment
        start_response: WSGI start_response function

    Returns:
        Response body

    """
    status = "200 OK"
    start_response(status, SECURITY_HEADERS)
    return [b'{"status":"ok"}']


class HealthServer:
    """Simple HTTP/HTTPS server for health checks."""

    def __init__(
        self,
        port: int = 8000,
        use_https: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
    ):
        """
        Initialize the health server.

        Args:
            port: Port to listen on
            use_https: Whether to use HTTPS
            cert_file: Path to SSL certificate file (required if use_https is True)
            key_file: Path to SSL key file (required if use_https is True)

        """
        self.port = port
        self.use_https = use_https
        self.cert_file = cert_file
        self.key_file = key_file
        self.server = None
        self.server_thread = None

        # Validate SSL configuration if HTTPS is enabled
        if self.use_https:
            if not self.cert_file or not self.key_file:
                logger.warning(
                    "HTTPS enabled but cert_file or key_file not provided. Falling back to HTTP."
                )
                self.use_https = False
            else:
                # Check if certificate and key files exist
                cert_path = Path(self.cert_file)
                key_path = Path(self.key_file)
                if not cert_path.exists() or not key_path.exists():
                    logger.warning(f"SSL certificate or key file not found. Falling back to HTTP.")
                    self.use_https = False

    def start(self):
        """Start the health server in a separate thread."""
        if self.server_thread is not None:
            return

        def run_server():
            self.server = make_server("", self.port, health_check_handler)

            # Configure SSL if HTTPS is enabled
            if self.use_https:
                try:
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    # Set minimum TLS version to TLS 1.2
                    context.minimum_version = ssl.TLSVersion.TLSv1_2
                    # Set recommended cipher suites
                    context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305')
                    context.load_cert_chain(self.cert_file, self.key_file)
                    self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
                    logger.info(f"Health server started with HTTPS on port {self.port}")
                except Exception as e:
                    logger.error(f"Failed to configure HTTPS: {e}. Falling back to HTTP.")
            else:
                logger.info(f"Health server started with HTTP on port {self.port}")

            self.server.serve_forever()

        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stop the health server."""
        if self.server is not None:
            self.server.shutdown()
            self.server = None

        if self.server_thread is not None:
            self.server_thread = None
