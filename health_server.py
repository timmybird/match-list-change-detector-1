#!/usr/bin/env python3

import os
import threading
from wsgiref.simple_server import make_server
from typing import Dict, Any, Callable

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
    status = '200 OK'
    headers = [('Content-type', 'application/json')]
    start_response(status, headers)
    return [b'{"status":"ok"}']

class HealthServer:
    """Simple HTTP server for health checks."""
    
    def __init__(self, port: int = 8000):
        """
        Initialize the health server.
        
        Args:
            port: Port to listen on
        """
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the health server in a separate thread."""
        if self.server_thread is not None:
            return
        
        def run_server():
            self.server = make_server('', self.port, health_check_handler)
            self.server.serve_forever()
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def stop(self):
        """Stop the health server."""
        if self.server is not None:
            self.server.shutdown()
            self.server = None
            self.server_thread = None
