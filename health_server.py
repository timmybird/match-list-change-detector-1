#!/usr/bin/env python3
"""
Simple health check server for the match list change detector.

Provides a basic HTTP/HTTPS server that responds to health check requests.
"""

# Apply Python 3.13+ compatibility fixes first
from python_compat import fix_python_313_imports

fix_python_313_imports()

import logging
import ssl
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Tuple, cast
from wsgiref.simple_server import make_server


# Define StartResponse type for WSGI
class StartResponse(Protocol):
    """Protocol for WSGI start_response callable."""

    def __call__(
        self, status: str, headers: List[Tuple[str, str]], exc_info: Optional[Any] = None
    ) -> None:
        """Call the start_response function."""
        ...


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
def health_check_handler(environ: Dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
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

    port: int
    use_https: bool
    cert_file: Optional[str]
    key_file: Optional[str]
    server: Optional[Any]
    server_thread: Optional[threading.Thread]

    def __init__(
        self,
        port: int = 8000,
        use_https: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
    ) -> None:
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

    def start(self) -> None:
        """Start the health server in a separate thread."""
        if self.server_thread is not None:
            return

        def run_server() -> None:
            # Use cast to satisfy mypy's type checking for the WSGI handler
            handler: Any = health_check_handler
            self.server = make_server(
                "", self.port, cast(Callable[[Dict[str, Any], Any], Iterable[bytes]], handler)
            )

            # Configure SSL if HTTPS is enabled
            if self.use_https and self.cert_file and self.key_file:
                try:
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    # Set minimum TLS version to TLS 1.2
                    context.minimum_version = ssl.TLSVersion.TLSv1_2
                    # Set recommended cipher suites
                    context.set_ciphers(
                        "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:"
                        "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:"
                        "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305"
                    )
                    context.load_cert_chain(self.cert_file, self.key_file)
                    if self.server and self.server.socket:
                        self.server.socket = context.wrap_socket(
                            self.server.socket, server_side=True
                        )
                        logger.info(f"Health server started with HTTPS on port {self.port}")
                except Exception as e:
                    logger.error(f"Failed to configure HTTPS: {e}. Falling back to HTTP.")
            else:
                logger.info(f"Health server started with HTTP on port {self.port}")

            if self.server:
                self.server.serve_forever()

        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self) -> None:
        """Stop the health server."""
        if self.server is not None:
            self.server.shutdown()
            self.server = None

        if self.server_thread is not None:
            self.server_thread = None
